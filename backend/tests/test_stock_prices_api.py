"""Tests for Stock Prices API Endpoints"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app
from models.company import Company
from models.financial import StockPrice


class TestStockPricesAPI:
    """Test Stock Prices API endpoints"""

    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)

    @pytest.fixture
    def sample_company(self, db_session: Session):
        """Sample company for testing"""
        company = Company(
            ticker_symbol="7203",
            edinet_code="E02144",
            company_name_jp="トヨタ自動車株式会社",
            company_name_en="Toyota Motor Corporation",
            market_division="Prime",
            industry_code="3050",
            industry_name="Transportation Equipment"
        )
        db_session.add(company)
        db_session.commit()
        db_session.refresh(company)
        return company

    @pytest.fixture
    def sample_stock_prices(self, db_session: Session, sample_company):
        """Sample stock price data"""
        prices = []
        base_date = date.today() - timedelta(days=10)
        
        for i in range(10):
            price_date = base_date + timedelta(days=i)
            price = StockPrice(
                company_id=sample_company.id,
                date=price_date,
                open_price=1500.0 + i,
                high_price=1520.0 + i,
                low_price=1480.0 + i,
                close_price=1510.0 + i,
                volume=1000000 + i * 10000,
                data_source="yahoo_finance"
            )
            prices.append(price)
            db_session.add(price)
        
        db_session.commit()
        return prices

    def test_get_latest_stock_price_from_db(self, client, sample_company, sample_stock_prices):
        """Test getting latest stock price from database"""
        response = client.get(f"/api/v1/stock-prices/{sample_company.ticker_symbol}/latest")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["ticker_symbol"] == sample_company.ticker_symbol
        assert data["current_price"] == 1519.0  # Latest close price
        assert data["open_price"] == 1509.0  # Latest open price
        assert data["currency"] == "JPY"
        assert "last_updated" in data

    def test_get_latest_stock_price_company_not_found(self, client):
        """Test getting latest stock price for non-existent company"""
        response = client.get("/api/v1/stock-prices/INVALID/latest")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_latest_stock_price_no_data(self, client, sample_company):
        """Test getting latest stock price when no price data exists"""
        response = client.get(f"/api/v1/stock-prices/{sample_company.ticker_symbol}/latest")
        
        assert response.status_code == 404
        assert "No price data found" in response.json()["detail"]

    @patch('core.dependencies.get_yahoo_finance_client')
    def test_get_latest_stock_price_live(self, mock_get_client, client, sample_company):
        """Test getting live stock price from Yahoo Finance"""
        # Mock Yahoo Finance client
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        
        mock_client.get_stock_price.return_value = {
            "ticker": "7203",
            "close_price": 1600.0,
            "open_price": 1580.0,
            "high_price": 1620.0,
            "low_price": 1570.0,
            "volume": 1200000,
            "previous_close": 1550.0,
            "market_cap": 20000000000,
            "currency": "JPY"
        }
        
        response = client.get(f"/api/v1/stock-prices/{sample_company.ticker_symbol}/latest?live=true")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["ticker_symbol"] == sample_company.ticker_symbol
        assert data["current_price"] == 1600.0
        assert data["previous_close"] == 1550.0
        assert data["change"] == 50.0  # 1600 - 1550
        assert abs(data["change_percent"] - 3.226) < 0.01  # (50/1550)*100

    @patch('core.dependencies.get_yahoo_finance_client')
    def test_get_latest_stock_price_live_error(self, mock_get_client, client, sample_company):
        """Test getting live stock price when Yahoo Finance fails"""
        # Mock Yahoo Finance client to return None
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.get_stock_price.return_value = None
        
        response = client.get(f"/api/v1/stock-prices/{sample_company.ticker_symbol}/latest?live=true")
        
        assert response.status_code == 503
        assert "Unable to fetch live price data" in response.json()["detail"]

    def test_get_historical_stock_prices(self, client, sample_company, sample_stock_prices):
        """Test getting historical stock prices"""
        response = client.get(f"/api/v1/stock-prices/{sample_company.ticker_symbol}/historical?days=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) <= 5  # Should return up to 5 days
        assert all(item["ticker_symbol"] == sample_company.ticker_symbol for item in data)
        assert all("date" in item for item in data)
        assert all("close_price" in item for item in data)

    def test_get_historical_stock_prices_with_dates(self, client, sample_company, sample_stock_prices):
        """Test getting historical stock prices with specific date range"""
        start_date = (date.today() - timedelta(days=5)).isoformat()
        end_date = date.today().isoformat()
        
        response = client.get(
            f"/api/v1/stock-prices/{sample_company.ticker_symbol}/historical"
            f"?start_date={start_date}&end_date={end_date}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all dates are within the specified range
        for item in data:
            item_date = datetime.strptime(item["date"], "%Y-%m-%d").date()
            assert datetime.strptime(start_date, "%Y-%m-%d").date() <= item_date <= datetime.strptime(end_date, "%Y-%m-%d").date()

    def test_get_historical_stock_prices_no_data(self, client, sample_company):
        """Test getting historical stock prices when no data exists"""
        response = client.get(f"/api/v1/stock-prices/{sample_company.ticker_symbol}/historical")
        
        assert response.status_code == 404
        assert "No historical price data found" in response.json()["detail"]

    def test_get_chart_data(self, client, sample_company, sample_stock_prices):
        """Test getting chart data"""
        response = client.get(f"/api/v1/stock-prices/{sample_company.ticker_symbol}/chart?period=1mo")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["ticker_symbol"] == sample_company.ticker_symbol
        assert data["period"] == "1mo"
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
        
        # Check chart data structure
        chart_point = data["data"][0]
        assert "date" in chart_point
        assert "open" in chart_point
        assert "high" in chart_point
        assert "low" in chart_point
        assert "close" in chart_point
        assert "volume" in chart_point

    def test_get_chart_data_invalid_period(self, client, sample_company):
        """Test getting chart data with invalid period"""
        response = client.get(f"/api/v1/stock-prices/{sample_company.ticker_symbol}/chart?period=invalid")
        
        assert response.status_code == 422  # Validation error

    def test_get_multiple_stock_prices(self, client, sample_company, sample_stock_prices):
        """Test getting stock prices for multiple tickers"""
        response = client.get(f"/api/v1/stock-prices/?tickers={sample_company.ticker_symbol}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["ticker_symbol"] == sample_company.ticker_symbol

    def test_get_multiple_stock_prices_too_many_tickers(self, client):
        """Test getting stock prices with too many tickers"""
        tickers = ",".join([f"TICK{i}" for i in range(51)])  # 51 tickers
        response = client.get(f"/api/v1/stock-prices/?tickers={tickers}")
        
        assert response.status_code == 400
        assert "Maximum 50 tickers allowed" in response.json()["detail"]

    def test_get_multiple_stock_prices_missing_tickers(self, client):
        """Test getting stock prices for non-existent tickers"""
        response = client.get("/api/v1/stock-prices/?tickers=INVALID1,INVALID2")
        
        assert response.status_code == 404
        assert "Companies not found" in response.json()["detail"]

    def test_historical_prices_date_validation(self, client, sample_company):
        """Test historical prices endpoint with invalid date parameters"""
        # Test with days parameter out of range
        response = client.get(f"/api/v1/stock-prices/{sample_company.ticker_symbol}/historical?days=500")
        assert response.status_code == 422  # Validation error
        
        response = client.get(f"/api/v1/stock-prices/{sample_company.ticker_symbol}/historical?days=0")
        assert response.status_code == 422  # Validation error

    def test_chart_data_all_periods(self, client, sample_company, sample_stock_prices):
        """Test chart data endpoint with all valid periods"""
        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"]
        
        for period in valid_periods:
            response = client.get(f"/api/v1/stock-prices/{sample_company.ticker_symbol}/chart?period={period}")
            
            # Some periods might not have data in our test dataset, but should not error
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["period"] == period

    def test_response_model_structure(self, client, sample_company, sample_stock_prices):
        """Test that response models have correct structure"""
        # Test latest price response
        response = client.get(f"/api/v1/stock-prices/{sample_company.ticker_symbol}/latest")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = [
            "ticker_symbol", "current_price", "open_price", "high_price", 
            "low_price", "volume", "currency", "last_updated"
        ]
        for field in required_fields:
            assert field in data
        
        # Test historical data response
        response = client.get(f"/api/v1/stock-prices/{sample_company.ticker_symbol}/historical?days=1")
        assert response.status_code == 200
        
        data = response.json()
        if data:  # If we have data
            item = data[0]
            required_fields = [
                "id", "company_id", "ticker_symbol", "date", "open_price",
                "high_price", "low_price", "close_price", "data_source", "created_at"
            ]
            for field in required_fields:
                assert field in item

    def test_error_handling(self, client):
        """Test API error handling"""
        # Test 404 for non-existent ticker
        response = client.get("/api/v1/stock-prices/NONEXISTENT/latest")
        assert response.status_code == 404
        assert "detail" in response.json()
        
        # Test invalid ticker format in path
        response = client.get("/api/v1/stock-prices/TOOLONGTICKERCODE123456/latest")
        assert response.status_code == 404  # Company not found