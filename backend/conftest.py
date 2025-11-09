"""
Test configuration and fixtures for pytest
"""

import os
import sys
from typing import Generator, Any
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import asyncio
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.company import Base as CompanyBase
from models.financial import Base as FinancialBase
from models.user import Base as UserBase
from api.main import app
from core.config import Settings
from core.database import get_db
from core.dependencies import get_redis_client
import redis


# Override settings for testing
@pytest.fixture(scope="session")
def test_settings():
    """Test settings fixture"""
    # Get database URL from environment or use default
    import os

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://stockcode:stockcode123@localhost:5432/stock_code_test",
    )
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")

    return Settings(
        database_url=database_url,
        redis_url=redis_url,
        edinet_api_key="test_api_key",
        secret_key="test_secret_key_for_testing_only",
        environment="test",
        cors_origins=["http://localhost:3000", "http://localhost:8000"],
        debug=True,
    )


# Database fixtures
@pytest.fixture(scope="session")
def test_engine(test_settings):
    """Create test database engine"""
    engine = create_engine(
        test_settings.database_url,
        poolclass=NullPool,  # Disable connection pooling for tests
        echo=False,
    )
    return engine


@pytest.fixture(scope="session")
def setup_database(test_engine):
    """Create all tables before tests, drop after"""
    # Create all tables
    CompanyBase.metadata.create_all(test_engine)
    FinancialBase.metadata.create_all(test_engine)
    UserBase.metadata.create_all(test_engine)
    yield
    # Drop all tables after tests
    UserBase.metadata.drop_all(test_engine)
    FinancialBase.metadata.drop_all(test_engine)
    CompanyBase.metadata.drop_all(test_engine)


@pytest.fixture(scope="function")
def db_session(test_engine, setup_database) -> Generator[Session, None, None]:
    """Create a new database session for each test"""
    SessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    session = SessionLocal()

    yield session

    session.close()

    # Clean up all tables after test
    from models.user import User
    from models.company import Company
    from models.financial import FinancialStatement, FinancialIndicator, StockPrice

    session = SessionLocal()
    try:
        session.query(User).delete()
        session.query(FinancialIndicator).delete()
        session.query(StockPrice).delete()
        session.query(FinancialStatement).delete()
        session.query(Company).delete()
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()


# Redis fixtures
@pytest.fixture(scope="function")
def redis_client(test_settings):
    """Create Redis client for testing"""
    client = redis.from_url(test_settings.redis_url, decode_responses=True)
    yield client
    # Clean up Redis after test
    client.flushdb()
    client.close()


# API Client fixtures
@pytest.fixture(scope="function")
def client(db_session, redis_client) -> TestClient:
    """Create FastAPI test client"""

    def get_db_override():
        try:
            yield db_session
        finally:
            pass

    def get_redis_override():
        return redis_client

    app.dependency_overrides[get_db] = get_db_override
    app.dependency_overrides[get_redis_client] = get_redis_override

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# Mock fixtures for external services
@pytest.fixture
def mock_edinet_api():
    """Mock EDINET API client"""
    with patch("services.edinet_client.EdinetClient") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance

        # Setup default responses
        mock_instance.search_documents.return_value = {
            "results": [
                {
                    "docID": "S100TEST",
                    "edinetCode": "E00001",
                    "filerName": "テスト株式会社",
                    "periodStart": "2023-04-01",
                    "periodEnd": "2024-03-31",
                    "docTypeCode": "120",  # 有価証券報告書
                }
            ]
        }

        mock_instance.get_document.return_value = b"<XBRL>test data</XBRL>"

        yield mock_instance


@pytest.fixture
def mock_yahoo_finance():
    """Mock Yahoo Finance API"""
    with patch("yfinance.Ticker") as mock:
        mock_ticker = Mock()
        mock.return_value = mock_ticker

        # Setup default responses
        mock_ticker.info = {
            "previousClose": 1500.0,
            "marketCap": 1000000000,
            "trailingPE": 15.0,
            "forwardPE": 14.0,
            "dividendYield": 0.02,
        }

        mock_ticker.history.return_value = Mock(Close=[1450, 1480, 1500])

        yield mock_ticker


# Sample data fixtures
@pytest.fixture
def sample_company_data():
    """Sample company data for testing"""
    return {
        "ticker_symbol": "7203",
        "edinet_code": "E02144",
        "company_name_jp": "トヨタ自動車株式会社",
        "company_name_en": "Toyota Motor Corporation",
        "market_division": "Prime",
        "industry_code": "3050",
        "industry_name": "Transportation Equipment",
        "founding_date": datetime(1937, 8, 28),
        "listing_date": datetime(1949, 5, 16),
        "fiscal_year_end": "03-31",
        "employee_count": 372817,
        "market_cap": 40000000000000,  # 40 trillion yen
        "shares_outstanding": 13974943300,
        "description": "Global automotive manufacturer",
        "website_url": "https://www.toyota.co.jp",
        "headquarters_address": "愛知県豊田市トヨタ町1番地",
    }


@pytest.fixture
def sample_financial_data():
    """Sample financial statement data for testing"""
    return {
        "company_id": 1,
        "fiscal_year": 2024,
        "fiscal_quarter": 4,
        "report_type": "annual",
        "revenue": 31379507000000,  # 31.4 trillion yen
        "operating_income": 2725359000000,  # 2.7 trillion yen
        "net_income": 2451318000000,  # 2.5 trillion yen
        "total_assets": 67688771000000,  # 67.7 trillion yen
        "total_liabilities": 41081802000000,  # 41.1 trillion yen
        "shareholders_equity": 26606969000000,  # 26.6 trillion yen
        "cash_flow_operating": 4506500000000,  # 4.5 trillion yen
        "cash_flow_investing": -3875700000000,  # -3.9 trillion yen
        "cash_flow_financing": -789900000000,  # -790 billion yen
        "eps": 175.44,
        "bps": 1902.37,
        "dividend_per_share": 35.00,
    }


@pytest.fixture
def sample_xbrl_data():
    """Sample XBRL data for testing"""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <xbrl xmlns="http://www.xbrl.org/2003/instance">
        <context id="CurrentYearInstant">
            <entity>
                <identifier scheme="http://disclosure.edinet-fsa.go.jp">E02144</identifier>
            </entity>
            <period>
                <instant>2024-03-31</instant>
            </period>
        </context>
        <context id="CurrentYearDuration">
            <entity>
                <identifier scheme="http://disclosure.edinet-fsa.go.jp">E02144</identifier>
            </entity>
            <period>
                <startDate>2023-04-01</startDate>
                <endDate>2024-03-31</endDate>
            </period>
        </context>
        <NetSales contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">31379507000000</NetSales>
        <OperatingIncome contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">2725359000000</OperatingIncome>
        <NetIncome contextRef="CurrentYearDuration" decimals="-6" unitRef="JPY">2451318000000</NetIncome>
        <TotalAssets contextRef="CurrentYearInstant" decimals="-6" unitRef="JPY">67688771000000</TotalAssets>
        <ShareholdersEquity contextRef="CurrentYearInstant" decimals="-6" unitRef="JPY">26606969000000</ShareholdersEquity>
    </xbrl>"""


# Async test support
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Utility fixtures
@pytest.fixture
def auth_headers():
    """Generate authentication headers for testing"""
    return {"Authorization": "Bearer test_token_12345"}


# Markers for test organization
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require external dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that may require database or API"
    )
    config.addinivalue_line("markers", "slow: Tests that take longer than usual to run")
    config.addinivalue_line(
        "markers", "requires_db: Tests that require database connection"
    )
    config.addinivalue_line(
        "markers", "requires_api: Tests that require external API access"
    )
