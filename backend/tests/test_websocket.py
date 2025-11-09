"""Tests for WebSocket real-time price updates"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime
from decimal import Decimal

from models.user import User
from models.company import Company
from models.watchlist import Watchlist, WatchlistItem
from core.sessions import create_session
from api.routers.websocket import (
    ConnectionManager,
    get_websocket_user,
    verify_watchlist_access,
    fetch_watchlist_prices,
)


# Fixtures

@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        google_id="ws_test_user",
        email="ws_test@example.com",
        name="WebSocket Test User",
        role="free",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_company(db_session):
    """Create a test company"""
    company = Company(
        ticker_symbol="7203",
        edinet_code="E00000",
        company_name_jp="トヨタ自動車株式会社",
        company_name_en="Toyota Motor Corporation",
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def test_company_2(db_session):
    """Create a second test company"""
    company = Company(
        ticker_symbol="9984",
        edinet_code="E00001",
        company_name_jp="ソフトバンクグループ株式会社",
        company_name_en="SoftBank Group Corp.",
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def test_watchlist(db_session, test_user, test_company, test_company_2):
    """Create a test watchlist with items"""
    watchlist = Watchlist(
        user_id=test_user.id,
        name="My Portfolio",
        description="Test portfolio",
        is_public=False,
        display_order=0,
    )
    db_session.add(watchlist)
    db_session.commit()
    db_session.refresh(watchlist)

    # Add items to watchlist
    item1 = WatchlistItem(
        watchlist_id=watchlist.id,
        company_id=test_company.id,
        display_order=0,
        quantity=Decimal("100"),
        purchase_price=Decimal("2400.00"),
        memo="Toyota position",
        tags=["automotive", "japan"],
    )
    item2 = WatchlistItem(
        watchlist_id=watchlist.id,
        company_id=test_company_2.id,
        display_order=1,
        quantity=Decimal("50"),
        purchase_price=Decimal("5000.00"),
        memo="SoftBank position",
        tags=["tech", "telecom"],
    )
    db_session.add_all([item1, item2])
    db_session.commit()

    return watchlist


@pytest.fixture
def public_watchlist(db_session, test_user, test_company):
    """Create a public watchlist"""
    watchlist = Watchlist(
        user_id=test_user.id,
        name="Public Watchlist",
        description="Public test watchlist",
        is_public=True,
        display_order=0,
    )
    db_session.add(watchlist)
    db_session.commit()
    db_session.refresh(watchlist)

    item = WatchlistItem(
        watchlist_id=watchlist.id,
        company_id=test_company.id,
        display_order=0,
    )
    db_session.add(item)
    db_session.commit()

    return watchlist


@pytest.fixture
def session_token(test_user, redis_client):
    """Create a valid session token"""
    return create_session(test_user.id, redis_client)


# Unit Tests

class TestConnectionManager:
    """Test the ConnectionManager class"""

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self):
        """Test connecting and disconnecting WebSocket"""
        manager = ConnectionManager()
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()

        watchlist_id = 1

        # Connect
        await manager.connect(mock_websocket, watchlist_id)
        assert watchlist_id in manager.active_connections
        assert mock_websocket in manager.active_connections[watchlist_id]
        mock_websocket.accept.assert_called_once()

        # Disconnect
        await manager.disconnect(mock_websocket, watchlist_id)
        assert watchlist_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_multiple_connections(self):
        """Test multiple connections to the same watchlist"""
        manager = ConnectionManager()
        mock_ws1 = Mock()
        mock_ws1.accept = AsyncMock()
        mock_ws2 = Mock()
        mock_ws2.accept = AsyncMock()

        watchlist_id = 1

        await manager.connect(mock_ws1, watchlist_id)
        await manager.connect(mock_ws2, watchlist_id)

        assert len(manager.active_connections[watchlist_id]) == 2

        await manager.disconnect(mock_ws1, watchlist_id)
        assert len(manager.active_connections[watchlist_id]) == 1

        await manager.disconnect(mock_ws2, watchlist_id)
        assert watchlist_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending message to specific WebSocket"""
        manager = ConnectionManager()
        mock_websocket = Mock()
        mock_websocket.send_json = AsyncMock()

        message = {"type": "test", "data": "hello"}
        await manager.send_personal_message(message, mock_websocket)

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_watchlist(self):
        """Test broadcasting message to all watchlist connections"""
        manager = ConnectionManager()
        mock_ws1 = Mock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_json = AsyncMock()
        mock_ws2 = Mock()
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_json = AsyncMock()

        watchlist_id = 1

        await manager.connect(mock_ws1, watchlist_id)
        await manager.connect(mock_ws2, watchlist_id)

        message = {"type": "price_update", "data": "test"}
        await manager.broadcast_to_watchlist(message, watchlist_id)

        mock_ws1.send_json.assert_called_once_with(message)
        mock_ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_handles_disconnected_clients(self):
        """Test that broadcast removes disconnected clients"""
        manager = ConnectionManager()
        mock_ws_good = Mock()
        mock_ws_good.accept = AsyncMock()
        mock_ws_good.send_json = AsyncMock()
        mock_ws_bad = Mock()
        mock_ws_bad.accept = AsyncMock()
        mock_ws_bad.send_json = AsyncMock(side_effect=Exception("Connection lost"))

        watchlist_id = 1

        await manager.connect(mock_ws_good, watchlist_id)
        await manager.connect(mock_ws_bad, watchlist_id)

        message = {"type": "test"}
        await manager.broadcast_to_watchlist(message, watchlist_id)

        # Good websocket should receive message
        mock_ws_good.send_json.assert_called_once()

        # Bad websocket should be removed
        assert mock_ws_bad not in manager.active_connections[watchlist_id]


class TestWebSocketAuthentication:
    """Test WebSocket authentication"""

    @pytest.mark.asyncio
    async def test_verify_watchlist_access_owner(self, db_session, test_user, test_watchlist):
        """Test watchlist access verification for owner"""
        watchlist = await verify_watchlist_access(
            test_watchlist.id,
            test_user,
            db_session
        )
        assert watchlist is not None
        assert watchlist.id == test_watchlist.id

    @pytest.mark.asyncio
    async def test_verify_watchlist_access_public(self, db_session, public_watchlist):
        """Test watchlist access verification for public watchlist"""
        # Create another user
        other_user = User(
            google_id="other_user",
            email="other@example.com",
            name="Other User",
            role="free",
            is_active=True,
        )
        db_session.add(other_user)
        db_session.commit()

        watchlist = await verify_watchlist_access(
            public_watchlist.id,
            other_user,
            db_session
        )
        assert watchlist is not None
        assert watchlist.is_public is True

    @pytest.mark.asyncio
    async def test_verify_watchlist_access_denied(self, db_session, test_watchlist):
        """Test watchlist access denied for non-owner"""
        other_user = User(
            google_id="other_user_2",
            email="other2@example.com",
            name="Other User 2",
            role="free",
            is_active=True,
        )
        db_session.add(other_user)
        db_session.commit()

        watchlist = await verify_watchlist_access(
            test_watchlist.id,
            other_user,
            db_session
        )
        assert watchlist is None

    @pytest.mark.asyncio
    async def test_verify_watchlist_not_found(self, db_session, test_user):
        """Test watchlist access with non-existent watchlist"""
        watchlist = await verify_watchlist_access(
            99999,
            test_user,
            db_session
        )
        assert watchlist is None


class TestFetchWatchlistPrices:
    """Test price fetching functionality"""

    @pytest.mark.asyncio
    async def test_fetch_prices_empty_watchlist(self, db_session, test_user):
        """Test fetching prices for empty watchlist"""
        empty_watchlist = Watchlist(
            user_id=test_user.id,
            name="Empty Watchlist",
            description="No stocks",
            is_public=False,
            display_order=0,
        )
        db_session.add(empty_watchlist)
        db_session.commit()
        db_session.refresh(empty_watchlist)

        mock_yahoo_client = Mock()

        result = await fetch_watchlist_prices(
            empty_watchlist,
            mock_yahoo_client,
            db_session
        )

        assert result["type"] == "price_update"
        assert result["watchlist_id"] == empty_watchlist.id
        assert result["stocks"] == []
        assert result["timestamp"] is None

    @pytest.mark.asyncio
    async def test_fetch_prices_with_data(self, db_session, test_watchlist, test_company, test_company_2):
        """Test fetching prices with actual data"""
        mock_yahoo_client = Mock()
        mock_yahoo_client.bulk_fetch_prices = AsyncMock(return_value={
            "7203": {
                "ticker": "7203",
                "close_price": 2500.0,
                "previous_close": 2450.0,
                "currency": "JPY",
            },
            "9984": {
                "ticker": "9984",
                "close_price": 5200.0,
                "previous_close": 5000.0,
                "currency": "JPY",
            }
        })

        result = await fetch_watchlist_prices(
            test_watchlist,
            mock_yahoo_client,
            db_session
        )

        assert result["type"] == "price_update"
        assert result["watchlist_id"] == test_watchlist.id
        assert len(result["stocks"]) == 2
        assert result["timestamp"] is not None

        # Check Toyota data
        toyota_stock = next(s for s in result["stocks"] if s["ticker_symbol"] == "7203")
        assert toyota_stock["current_price"] == 2500.0
        assert toyota_stock["change"] == 50.0
        assert toyota_stock["change_percent"] == pytest.approx(2.04, rel=0.1)
        assert toyota_stock["quantity"] == 100.0
        assert toyota_stock["purchase_price"] == 2400.0
        assert toyota_stock["unrealized_pl"] == 10000.0  # (2500 - 2400) * 100

        # Check SoftBank data
        softbank_stock = next(s for s in result["stocks"] if s["ticker_symbol"] == "9984")
        assert softbank_stock["current_price"] == 5200.0
        assert softbank_stock["change"] == 200.0
        assert softbank_stock["change_percent"] == 4.0
        assert softbank_stock["quantity"] == 50.0
        assert softbank_stock["unrealized_pl"] == 10000.0  # (5200 - 5000) * 50

    @pytest.mark.asyncio
    async def test_fetch_prices_partial_data(self, db_session, test_watchlist):
        """Test fetching prices when some stocks have no data"""
        mock_yahoo_client = Mock()
        mock_yahoo_client.bulk_fetch_prices = AsyncMock(return_value={
            "7203": {
                "ticker": "7203",
                "close_price": 2500.0,
                "previous_close": 2450.0,
            },
            "9984": None,  # No data for this stock
        })

        result = await fetch_watchlist_prices(
            test_watchlist,
            mock_yahoo_client,
            db_session
        )

        assert len(result["stocks"]) == 2

        # Toyota should have data
        toyota_stock = next(s for s in result["stocks"] if s["ticker_symbol"] == "7203")
        assert toyota_stock["current_price"] == 2500.0

        # SoftBank should have None for price fields
        softbank_stock = next(s for s in result["stocks"] if s["ticker_symbol"] == "9984")
        assert softbank_stock["current_price"] is None
        assert softbank_stock["change"] is None


# Integration Tests

@pytest.mark.asyncio
async def test_websocket_connection_with_auth(client, test_user, test_watchlist, redis_client, db_session):
    """Test WebSocket connection with authentication"""
    session_token = create_session(test_user.id, redis_client)

    with patch("api.routers.websocket.fetch_watchlist_prices") as mock_fetch:
        mock_fetch.return_value = {
            "type": "price_update",
            "watchlist_id": test_watchlist.id,
            "stocks": [],
            "timestamp": datetime.now().isoformat()
        }

        with client.websocket_connect(
            f"/api/v1/ws/watchlist/{test_watchlist.id}/prices?token={session_token}"
        ) as websocket:
            # Should receive initial price data
            data = websocket.receive_json()
            assert data["type"] == "price_update"
            assert data["watchlist_id"] == test_watchlist.id


@pytest.mark.asyncio
async def test_websocket_connection_without_auth(client, test_watchlist):
    """Test WebSocket connection fails without authentication"""
    with pytest.raises(Exception):  # FastAPI WebSocketDisconnect
        with client.websocket_connect(
            f"/api/v1/ws/watchlist/{test_watchlist.id}/prices"
        ) as websocket:
            pass


@pytest.mark.asyncio
async def test_websocket_connection_invalid_token(client, test_watchlist):
    """Test WebSocket connection fails with invalid token"""
    with pytest.raises(Exception):
        with client.websocket_connect(
            f"/api/v1/ws/watchlist/{test_watchlist.id}/prices?token=invalid_token"
        ) as websocket:
            pass


@pytest.mark.asyncio
async def test_websocket_access_denied(client, test_user, test_watchlist, redis_client, db_session):
    """Test WebSocket connection denied for non-owner"""
    # Create another user
    other_user = User(
        google_id="other_ws_user",
        email="other_ws@example.com",
        name="Other WS User",
        role="free",
        is_active=True,
    )
    db_session.add(other_user)
    db_session.commit()

    session_token = create_session(other_user.id, redis_client)

    with pytest.raises(Exception):
        with client.websocket_connect(
            f"/api/v1/ws/watchlist/{test_watchlist.id}/prices?token={session_token}"
        ) as websocket:
            pass
