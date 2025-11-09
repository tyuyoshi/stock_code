"""WebSocket router for real-time stock price updates"""

import asyncio
import logging
from typing import Optional, Dict, Any, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_redis_client
from models.watchlist import Watchlist, WatchlistItem
from models.user import User
from services.yahoo_finance_client import YahooFinanceClient
from redis import Redis
from core.sessions import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ws", tags=["websocket"])


class ConnectionManager:
    """Manage WebSocket connections for real-time price updates

    Uses centralized background tasks per watchlist to prevent memory leaks
    and reduce API calls. Only one price update task runs per watchlist,
    regardless of the number of connected clients.
    """

    def __init__(self):
        # Map of watchlist_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Map of watchlist_id -> asyncio.Task (background price update tasks)
        self.background_tasks: Dict[int, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        watchlist_id: int,
        watchlist,
        yahoo_client,
    ):
        """Accept and register a new WebSocket connection

        Starts a centralized background task for price updates if this is
        the first connection to the watchlist.

        Args:
            websocket: WebSocket connection to register
            watchlist_id: ID of the watchlist
            watchlist: Watchlist model instance
            yahoo_client: YahooFinanceClient instance
        """
        # Note: websocket.accept() is called in watchlist_price_stream() before this
        async with self._lock:
            if watchlist_id not in self.active_connections:
                self.active_connections[watchlist_id] = set()
            self.active_connections[watchlist_id].add(websocket)

            # Start background task only if this is the first connection
            if watchlist_id not in self.background_tasks:
                task = asyncio.create_task(
                    self._price_update_worker(watchlist_id, watchlist, yahoo_client)
                )
                self.background_tasks[watchlist_id] = task
                logger.info(
                    f"Started background price update task for watchlist {watchlist_id}"
                )

        logger.info(
            f"WebSocket connected for watchlist {watchlist_id}. "
            f"Total connections: {len(self.active_connections[watchlist_id])}"
        )

    async def disconnect(self, websocket: WebSocket, watchlist_id: int):
        """Remove a WebSocket connection

        Stops the background task if this is the last connection to the watchlist.

        Args:
            websocket: WebSocket connection to remove
            watchlist_id: ID of the watchlist
        """
        async with self._lock:
            if watchlist_id in self.active_connections:
                self.active_connections[watchlist_id].discard(websocket)
                if not self.active_connections[watchlist_id]:
                    del self.active_connections[watchlist_id]

                    # Stop background task if no more connections
                    if watchlist_id in self.background_tasks:
                        task = self.background_tasks[watchlist_id]
                        task.cancel()
                        del self.background_tasks[watchlist_id]
                        logger.info(
                            f"Stopped background price update task for watchlist {watchlist_id}"
                        )

        logger.info(f"WebSocket disconnected from watchlist {watchlist_id}")

    async def _price_update_worker(self, watchlist_id: int, watchlist, yahoo_client):
        """Background worker that periodically fetches and broadcasts prices

        This runs as a single task per watchlist, regardless of how many
        clients are connected. Prevents duplicate API calls and memory leaks.

        Creates a fresh database session for each iteration to prevent
        connection pool exhaustion in long-running background tasks.

        Args:
            watchlist_id: ID of the watchlist
            watchlist: Watchlist model instance
            yahoo_client: YahooFinanceClient instance
        """
        try:
            while True:
                # Check if there are still active connections
                async with self._lock:
                    if watchlist_id not in self.active_connections:
                        logger.info(
                            f"No active connections for watchlist {watchlist_id}, stopping worker"
                        )
                        break

                # Create fresh DB session for this iteration
                db = next(get_db())
                try:
                    # Fetch prices once for all connections
                    price_data = await fetch_watchlist_prices(
                        watchlist, yahoo_client, db
                    )
                    await self.broadcast_to_watchlist(price_data, watchlist_id)
                except Exception as e:
                    logger.error(
                        f"Error fetching prices for watchlist {watchlist_id}: {e}"
                    )
                finally:
                    # Always close DB session to prevent connection pool exhaustion
                    db.close()

                # Wait 5 seconds before next update
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info(f"Price update worker cancelled for watchlist {watchlist_id}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in price update worker for watchlist {watchlist_id}: {e}"
            )
        finally:
            # Cleanup on exit
            async with self._lock:
                if watchlist_id in self.background_tasks:
                    del self.background_tasks[watchlist_id]

    async def send_personal_message(
        self, message: Dict[str, Any], websocket: WebSocket
    ):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message to WebSocket: {e}")

    async def broadcast_to_watchlist(self, message: Dict[str, Any], watchlist_id: int):
        """Broadcast a message to all connections for a watchlist"""
        async with self._lock:
            if watchlist_id not in self.active_connections:
                return

            connections = list(self.active_connections[watchlist_id])

        # Send to all connections (outside the lock to avoid blocking)
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        if disconnected:
            async with self._lock:
                for connection in disconnected:
                    self.active_connections[watchlist_id].discard(connection)


# Global connection manager
manager = ConnectionManager()


async def get_websocket_user(
    websocket: WebSocket,
    db: Session,
    redis_client: Redis,
) -> Optional[User]:
    """Authenticate WebSocket connection using short-lived token

    Args:
        websocket: WebSocket connection
        db: Database session
        redis_client: Redis client

    Returns:
        Authenticated user or None if authentication fails
    """
    # Extract token from query parameters
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token"
        )
        return None

    if not redis_client:
        await websocket.close(
            code=status.WS_1011_INTERNAL_ERROR, reason="Session service unavailable"
        )
        return None

    # Validate token from Redis
    redis_key = f"ws_token:{token}"
    user_id_str = redis_client.get(redis_key)

    if not user_id_str:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token"
        )
        return None

    # Delete token (one-time use for security)
    redis_client.delete(redis_key)

    try:
        user_id = int(user_id_str)
    except ValueError:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token data"
        )
        return None

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="User not found"
        )
        return None

    if not user.is_active:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="User account is inactive"
        )
        return None

    return user


async def verify_watchlist_access(
    watchlist_id: int, user: User, db: Session
) -> Optional[Watchlist]:
    """Verify user has access to the watchlist

    Args:
        watchlist_id: ID of the watchlist
        user: Authenticated user
        db: Database session

    Returns:
        Watchlist if user has access, None otherwise
    """
    watchlist = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()

    if not watchlist:
        return None

    # Check if user owns the watchlist or if it's public
    if watchlist.user_id != user.id and not watchlist.is_public:
        return None

    return watchlist


async def fetch_watchlist_prices(
    watchlist: Watchlist, yahoo_client: YahooFinanceClient, db: Session
) -> Dict[str, Any]:
    """Fetch current prices for all stocks in a watchlist

    Args:
        watchlist: Watchlist object
        yahoo_client: Yahoo Finance client
        db: Database session

    Returns:
        Dictionary with price data
    """
    # Get all stocks in the watchlist with company data
    items = (
        db.query(WatchlistItem).filter(WatchlistItem.watchlist_id == watchlist.id).all()
    )

    if not items:
        return {
            "type": "price_update",
            "watchlist_id": watchlist.id,
            "stocks": [],
            "timestamp": None,
        }

    # Extract ticker symbols from companies
    from models.company import Company

    company_ids = [item.company_id for item in items]
    companies = db.query(Company).filter(Company.id.in_(company_ids)).all()
    company_map = {c.id: c for c in companies}

    ticker_symbols = [
        company_map[item.company_id].ticker_symbol
        for item in items
        if item.company_id in company_map
    ]

    # Fetch prices in bulk
    price_data = await yahoo_client.bulk_fetch_prices(ticker_symbols)

    # Build response
    stocks = []
    for item in items:
        if item.company_id not in company_map:
            continue

        company = company_map[item.company_id]
        ticker = company.ticker_symbol
        price_info = price_data.get(ticker)

        stock_data = {
            "company_id": company.id,
            "ticker_symbol": ticker,
            "company_name": company.company_name_jp or company.company_name_en,
            "current_price": None,
            "change": None,
            "change_percent": None,
            "quantity": float(item.quantity) if item.quantity else None,
            "purchase_price": (
                float(item.purchase_price) if item.purchase_price else None
            ),
        }

        if price_info:
            current_price = price_info.get("close_price")
            previous_close = price_info.get("previous_close")

            stock_data["current_price"] = current_price

            if current_price and previous_close:
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100
                stock_data["change"] = round(change, 2)
                stock_data["change_percent"] = round(change_percent, 2)

            # Calculate P&L if user has position
            if item.quantity and item.purchase_price and current_price:
                unrealized_pl = (current_price - float(item.purchase_price)) * float(
                    item.quantity
                )
                stock_data["unrealized_pl"] = round(unrealized_pl, 2)

        stocks.append(stock_data)

    from datetime import datetime

    return {
        "type": "price_update",
        "watchlist_id": watchlist.id,
        "stocks": stocks,
        "timestamp": datetime.now().isoformat(),
    }


@router.websocket("/watchlist/{watchlist_id}/prices")
async def watchlist_price_stream(
    websocket: WebSocket,
    watchlist_id: int,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis_client),
):
    """WebSocket endpoint for real-time stock price updates

    Uses centralized background tasks to prevent memory leaks.
    Each watchlist has only one price update task, shared by all connections.

    Authentication:
        Requires a short-lived token obtained from GET /api/v1/auth/ws-token
        Token should be passed as a query parameter: ?token=xxx
        Tokens are valid for 60 seconds and can only be used once.

    Message Format:
        {
            "type": "price_update",
            "watchlist_id": 123,
            "stocks": [
                {
                    "company_id": 1,
                    "ticker_symbol": "7203",
                    "company_name": "Toyota Motor Corp",
                    "current_price": 2500.0,
                    "change": 50.0,
                    "change_percent": 2.04,
                    "quantity": 100,
                    "purchase_price": 2400.0,
                    "unrealized_pl": 10000.0
                }
            ],
            "timestamp": "2025-11-09T12:00:00"
        }
    """
    # Accept the connection first (required by FastAPI)
    await websocket.accept()

    # Authenticate user
    user = await get_websocket_user(websocket, db=db, redis_client=redis_client)
    if not user:
        return  # Connection already closed with appropriate reason

    # Verify watchlist access
    watchlist = await verify_watchlist_access(watchlist_id, user, db)
    if not watchlist:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Watchlist not found or access denied",
        )
        return

    # Initialize Yahoo Finance client
    yahoo_client = YahooFinanceClient(redis_client=redis_client)

    # Send initial price data immediately before connecting
    try:
        initial_data = await fetch_watchlist_prices(watchlist, yahoo_client, db)
    except Exception as e:
        logger.error(f"Error fetching initial prices for watchlist {watchlist_id}: {e}")
        await websocket.close(
            code=status.WS_1011_INTERNAL_ERROR, reason="Failed to fetch initial data"
        )
        return

    # Connect the WebSocket (starts background task if first connection)
    await manager.connect(websocket, watchlist_id, watchlist, yahoo_client)

    try:
        # Send initial data to this connection
        await manager.send_personal_message(initial_data, websocket)

        # Keep connection alive and listen for client messages (ping/pong, heartbeat)
        # The background task handles all price updates via broadcast
        while True:
            try:
                # Wait for client messages with timeout
                # This keeps the connection alive and allows graceful disconnection
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                logger.debug(f"Received message from client: {data}")
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    # Connection lost
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for watchlist {watchlist_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket connection for watchlist {watchlist_id}: {e}")
        try:
            await websocket.close(
                code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error"
            )
        except Exception:
            pass
    finally:
        await manager.disconnect(websocket, watchlist_id)
