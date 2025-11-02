"""Tests for Yahoo Finance Client"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, date
import pandas as pd

from services.yahoo_finance_client import YahooFinanceClient


class TestYahooFinanceClient:
    """Test Yahoo Finance Client functionality"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        mock_redis = Mock()
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        return mock_redis

    @pytest.fixture
    def yahoo_client(self, mock_redis):
        """Yahoo Finance client with mock Redis"""
        return YahooFinanceClient(redis_client=mock_redis)

    @pytest.fixture
    def yahoo_client_no_redis(self):
        """Yahoo Finance client without Redis"""
        return YahooFinanceClient(redis_client=None)

    def test_format_ticker(self, yahoo_client):
        """Test ticker formatting for Japanese stocks"""
        # Should add .T suffix
        assert yahoo_client._format_ticker("7203") == "7203.T"
        
        # Should not add if already present
        assert yahoo_client._format_ticker("7203.T") == "7203.T"
        
        # Should handle other formats
        assert yahoo_client._format_ticker("9984") == "9984.T"

    def test_cache_key_generation(self, yahoo_client):
        """Test cache key generation"""
        key = yahoo_client._get_cache_key("7203.T", "price")
        assert key == "yahoo_finance:7203.T:price"
        
        key = yahoo_client._get_cache_key("9984.T", "info")
        assert key == "yahoo_finance:9984.T:info"

    @pytest.mark.asyncio
    async def test_get_cached_data_no_redis(self, yahoo_client_no_redis):
        """Test cache operations without Redis"""
        # Should return None when no Redis
        result = await yahoo_client_no_redis._get_cached_data("test_key")
        assert result is None
        
        # Should not raise error when setting cache
        await yahoo_client_no_redis._set_cached_data("test_key", {"test": "data"})

    @pytest.mark.asyncio
    async def test_get_cached_data_with_redis(self, yahoo_client, mock_redis):
        """Test cache operations with Redis"""
        import json
        
        # Test cache miss
        mock_redis.get.return_value = None
        result = await yahoo_client._get_cached_data("test_key")
        assert result is None
        
        # Test cache hit
        test_data = {"price": 1500.0, "ticker": "7203"}
        mock_redis.get.return_value = json.dumps(test_data)
        result = await yahoo_client._get_cached_data("test_key")
        assert result == test_data

    @pytest.mark.asyncio
    @patch('yfinance.Ticker')
    async def test_get_stock_price_success(self, mock_ticker_class, yahoo_client):
        """Test successful stock price retrieval"""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker_class.return_value = mock_ticker
        
        # Mock ticker.info
        mock_ticker.info = {
            'previousClose': 1500.0,
            'marketCap': 1000000000,
            'currency': 'JPY'
        }
        
        # Mock ticker.history
        hist_data = pd.DataFrame({
            'Open': [1450.0],
            'High': [1520.0],
            'Low': [1440.0],
            'Close': [1500.0],
            'Volume': [1000000]
        }, index=[datetime.now()])
        
        mock_ticker.history.return_value = hist_data
        
        # Test
        result = await yahoo_client.get_stock_price("7203")
        
        # Verify
        assert result is not None
        assert result['ticker'] == "7203"
        assert result['formatted_ticker'] == "7203.T"
        assert result['close_price'] == 1500.0
        assert result['open_price'] == 1450.0
        assert result['high_price'] == 1520.0
        assert result['low_price'] == 1440.0
        assert result['volume'] == 1000000
        assert result['previous_close'] == 1500.0
        assert result['market_cap'] == 1000000000
        assert result['currency'] == 'JPY'
        
        # Verify API was called correctly
        mock_ticker_class.assert_called_once_with("7203.T")
        mock_ticker.history.assert_called_once_with(period="2d")

    @pytest.mark.asyncio
    @patch('yfinance.Ticker')
    async def test_get_stock_price_no_data(self, mock_ticker_class, yahoo_client):
        """Test stock price retrieval with no data"""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker_class.return_value = mock_ticker
        
        # Mock empty history
        mock_ticker.history.return_value = pd.DataFrame()
        
        # Test
        result = await yahoo_client.get_stock_price("INVALID")
        
        # Verify
        assert result is None

    @pytest.mark.asyncio
    @patch('yfinance.Ticker')
    async def test_get_stock_price_exception(self, mock_ticker_class, yahoo_client):
        """Test stock price retrieval with exception"""
        # Setup mock to raise exception
        mock_ticker_class.side_effect = Exception("API Error")
        
        # Test
        result = await yahoo_client.get_stock_price("7203")
        
        # Verify
        assert result is None

    @pytest.mark.asyncio
    @patch('yfinance.Ticker')
    async def test_get_historical_data_success(self, mock_ticker_class, yahoo_client):
        """Test successful historical data retrieval"""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker_class.return_value = mock_ticker
        
        # Mock historical data
        dates = [
            datetime(2023, 1, 1),
            datetime(2023, 1, 2),
            datetime(2023, 1, 3)
        ]
        hist_data = pd.DataFrame({
            'Open': [1400.0, 1450.0, 1480.0],
            'High': [1450.0, 1480.0, 1520.0],
            'Low': [1390.0, 1440.0, 1470.0],
            'Close': [1440.0, 1470.0, 1500.0],
            'Volume': [900000, 950000, 1000000]
        }, index=dates)
        
        mock_ticker.history.return_value = hist_data
        
        # Test
        result = await yahoo_client.get_historical_data("7203", period="5y")
        
        # Verify
        assert result is not None
        assert len(result) == 3
        
        # Check first record
        first_record = result[0]
        assert first_record['ticker'] == "7203"
        assert first_record['date'] == "2023-01-01"
        assert first_record['open_price'] == 1400.0
        assert first_record['close_price'] == 1440.0
        
        # Verify API was called correctly
        mock_ticker_class.assert_called_once_with("7203.T")
        mock_ticker.history.assert_called_once_with(period="5y")

    @pytest.mark.asyncio
    @patch('yfinance.Ticker')
    async def test_get_historical_data_with_dates(self, mock_ticker_class, yahoo_client):
        """Test historical data retrieval with specific dates"""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker_class.return_value = mock_ticker
        mock_ticker.history.return_value = pd.DataFrame({
            'Open': [1400.0],
            'High': [1450.0],
            'Low': [1390.0],
            'Close': [1440.0],
            'Volume': [900000]
        }, index=[datetime(2023, 1, 1)])
        
        # Test
        await yahoo_client.get_historical_data(
            "7203", 
            start_date="2023-01-01", 
            end_date="2023-01-31"
        )
        
        # Verify API was called with date range
        mock_ticker.history.assert_called_once_with(
            start="2023-01-01", 
            end="2023-01-31"
        )

    @pytest.mark.asyncio
    @patch('yfinance.Ticker')
    async def test_get_company_info_success(self, mock_ticker_class, yahoo_client):
        """Test successful company info retrieval"""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker_class.return_value = mock_ticker
        
        mock_ticker.info = {
            'longName': 'Toyota Motor Corporation',
            'shortName': 'Toyota',
            'industry': 'Auto Manufacturers',
            'sector': 'Consumer Cyclical',
            'marketCap': 2000000000000,
            'sharesOutstanding': 1500000000,
            'currency': 'JPY',
            'exchange': 'TSE',
            'website': 'https://toyota.com',
            'longBusinessSummary': 'Toyota is a leading automaker...',
            'fullTimeEmployees': 366283
        }
        
        # Test
        result = await yahoo_client.get_company_info("7203")
        
        # Verify
        assert result is not None
        assert result['ticker'] == "7203"
        assert result['formatted_ticker'] == "7203.T"
        assert result['company_name'] == 'Toyota Motor Corporation'
        assert result['industry'] == 'Auto Manufacturers'
        assert result['sector'] == 'Consumer Cyclical'
        assert result['market_cap'] == 2000000000000
        assert result['shares_outstanding'] == 1500000000
        assert result['currency'] == 'JPY'
        assert result['exchange'] == 'TSE'
        assert result['website'] == 'https://toyota.com'
        assert result['employee_count'] == 366283

    @pytest.mark.asyncio
    @patch('yfinance.Ticker')
    async def test_get_dividends_success(self, mock_ticker_class, yahoo_client):
        """Test successful dividend data retrieval"""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker_class.return_value = mock_ticker
        
        # Mock dividend data
        dividend_dates = [
            datetime(2023, 3, 31),
            datetime(2023, 9, 30)
        ]
        mock_ticker.dividends = pd.Series([50.0, 60.0], index=dividend_dates)
        
        # Test
        result = await yahoo_client.get_dividends("7203", period="2y")
        
        # Verify
        assert result is not None
        assert len(result) == 2
        
        first_dividend = result[0]
        assert first_dividend['ticker'] == "7203"
        assert first_dividend['ex_date'] == "2023-03-31"
        assert first_dividend['dividend_amount'] == 50.0

    @pytest.mark.asyncio
    @patch('yfinance.Ticker')
    async def test_get_stock_splits_success(self, mock_ticker_class, yahoo_client):
        """Test successful stock split data retrieval"""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker_class.return_value = mock_ticker
        
        # Mock stock split data
        split_dates = [datetime(2022, 10, 1)]
        mock_ticker.splits = pd.Series([5.0], index=split_dates)  # 5:1 split
        
        # Test
        result = await yahoo_client.get_stock_splits("7203", period="5y")
        
        # Verify
        assert result is not None
        assert len(result) == 1
        
        split = result[0]
        assert split['ticker'] == "7203"
        assert split['split_date'] == "2022-10-01"
        assert split['split_ratio'] == 5.0

    @pytest.mark.asyncio
    async def test_bulk_fetch_prices(self, yahoo_client):
        """Test bulk price fetching"""
        # Mock the get_stock_price method
        async def mock_get_stock_price(ticker):
            if ticker == "7203":
                return {"ticker": "7203", "close_price": 1500.0}
            elif ticker == "9984":
                return {"ticker": "9984", "close_price": 2000.0}
            else:
                return None
        
        yahoo_client.get_stock_price = mock_get_stock_price
        
        # Test
        tickers = ["7203", "9984", "INVALID"]
        result = await yahoo_client.bulk_fetch_prices(tickers)
        
        # Verify
        assert len(result) == 3
        assert result["7203"] is not None
        assert result["7203"]["close_price"] == 1500.0
        assert result["9984"] is not None
        assert result["9984"]["close_price"] == 2000.0
        assert result["INVALID"] is None

    @pytest.mark.asyncio
    async def test_rate_limiting(self, yahoo_client):
        """Test that rate limiting delay is applied"""
        import time
        
        # Mock the get_stock_price to track timing
        original_sleep = asyncio.sleep
        sleep_calls = []
        
        async def mock_sleep(delay):
            sleep_calls.append(delay)
            # Don't actually sleep in tests
            pass
        
        with patch('asyncio.sleep', side_effect=mock_sleep):
            with patch('yfinance.Ticker') as mock_ticker_class:
                # Setup mock
                mock_ticker = Mock()
                mock_ticker_class.return_value = mock_ticker
                mock_ticker.info = {'previousClose': 1500.0}
                mock_ticker.history.return_value = pd.DataFrame({
                    'Open': [1450.0], 'Close': [1500.0]
                }, index=[datetime.now()])
                
                # Make two calls
                await yahoo_client.get_stock_price("7203")
                await yahoo_client.get_stock_price("9984")
                
                # Verify rate limiting was applied
                assert len(sleep_calls) >= 2
                assert sleep_calls[0] == 0.5  # Rate limit delay
                assert sleep_calls[1] == 0.5  # Rate limit delay