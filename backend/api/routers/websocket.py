"""WebSocket router for real-time stock price updates"""

import asyncio
import logging
from typing import Optional, Dict, Any, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
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
    """Manage WebSocket connections for real-time price updates"""

    def __init__(self):
        # Map of watchlist_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, watchlist_id: int):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        async with self._lock:
            if watchlist_id not in self.active_connections:
                self.active_connections[watchlist_id] = set()
            self.active_connections[watchlist_id].add(websocket)
        logger.info(f"WebSocket connected for watchlist {watchlist_id}. Total connections: {len(self.active_connections[watchlist_id])}")

    async def disconnect(self, websocket: WebSocket, watchlist_id: int):
        """Remove a WebSocket connection"""
        async with self._lock:
            if watchlist_id in self.active_connections:
                self.active_connections[watchlist_id].discard(websocket)
                if not self.active_connections[watchlist_id]:
                    del self.active_connections[watchlist_id]
        logger.info(f"WebSocket disconnected from watchlist {watchlist_id}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
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
    """Authenticate WebSocket connection using session token

    Args:
        websocket: WebSocket connection
        db: Database session
        redis_client: Redis client

    Returns:
        Authenticated user or None if authentication fails
    """
    # Extract session token from query parameters
    session_token = websocket.query_params.get("token")

    if not session_token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token")
        return None

    if not redis_client:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Session service unavailable")
        return None

    # Validate session
    session_data = get_session(session_token, redis_client)
    if not session_data:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired session")
        return None

    user_id = session_data.get("user_id")
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid session data")
        return None

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
        return None

    if not user.is_active:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User account is inactive")
        return None

    return user


async def verify_watchlist_access(
    watchlist_id: int,
    user: User,
    db: Session
) -> Optional[Watchlist]:
    """Verify user has access to the watchlist

    Args:
        watchlist_id: ID of the watchlist
        user: Authenticated user
        db: Database session

    Returns:
        Watchlist if user has access, None otherwise
    """
    watchlist = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id
    ).first()

    if not watchlist:
        return None

    # Check if user owns the watchlist or if it's public
    if watchlist.user_id != user.id and not watchlist.is_public:
        return None

    return watchlist


async def fetch_watchlist_prices(
    watchlist: Watchlist,
    yahoo_client: YahooFinanceClient,
    db: Session
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
    items = db.query(WatchlistItem).filter(
        WatchlistItem.watchlist_id == watchlist.id
    ).all()

    if not items:
        return {
            "type": "price_update",
            "watchlist_id": watchlist.id,
            "stocks": [],
            "timestamp": None
        }

    # Extract ticker symbols from companies
    from models.company import Company
    company_ids = [item.company_id for item in items]
    companies = db.query(Company).filter(Company.id.in_(company_ids)).all()
    company_map = {c.id: c for c in companies}

    ticker_symbols = [company_map[item.company_id].ticker_symbol for item in items if item.company_id in company_map]

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
            "purchase_price": float(item.purchase_price) if item.purchase_price else None,
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
                unrealized_pl = (current_price - float(item.purchase_price)) * float(item.quantity)
                stock_data["unrealized_pl"] = round(unrealized_pl, 2)

        stocks.append(stock_data)

    from datetime import datetime
    return {
        "type": "price_update",
        "watchlist_id": watchlist.id,
        "stocks": stocks,
        "timestamp": datetime.now().isoformat()
    }


@router.websocket("/watchlist/{watchlist_id}/prices")
async def watchlist_price_stream(
    websocket: WebSocket,
    watchlist_id: int,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis_client),
):
    """WebSocket endpoint for real-time stock price updates

    Query Parameters:
        token: Session token for authentication

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
    # Authenticate user
    user = await get_websocket_user(websocket, db=db, redis_client=redis_client)
    if not user:
        return  # Connection already closed with appropriate reason

    # Verify watchlist access
    watchlist = await verify_watchlist_access(watchlist_id, user, db)
    if not watchlist:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Watchlist not found or access denied")
        return

    # Connect the WebSocket
    await manager.connect(websocket, watchlist_id)

    # Initialize Yahoo Finance client
    yahoo_client = YahooFinanceClient(redis_client=redis_client)

    try:
        # Send initial price data immediately
        initial_data = await fetch_watchlist_prices(watchlist, yahoo_client, db)
        await manager.send_personal_message(initial_data, websocket)

        # Start price update loop (5-second intervals)
        while True:
            await asyncio.sleep(5)

            # Fetch updated prices
            price_data = await fetch_watchlist_prices(watchlist, yahoo_client, db)

            # Broadcast to all connections for this watchlist
            await manager.broadcast_to_watchlist(price_data, watchlist_id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for watchlist {watchlist_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket price stream for watchlist {watchlist_id}: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        except:
            pass
    finally:
        await manager.disconnect(websocket, watchlist_id)
