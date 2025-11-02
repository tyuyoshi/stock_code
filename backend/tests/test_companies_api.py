"""Test cases for companies API endpoints"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.main import app
from core.database import get_db, Base
from models.company import Company
from models.financial import FinancialIndicator

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_companies.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="function")
def client():
    return TestClient(app)


@pytest.fixture
def sample_companies(db_session):
    """Create sample companies for testing"""
    companies = [
        Company(
            id=1,
            ticker_symbol="7203",
            company_name_jp="トヨタ自動車",
            company_name_en="Toyota Motor Corporation",
            market_division="Prime",
            industry_name="輸送用機器",
            market_cap=35000000,  # 35兆円
            employee_count=70000
        ),
        Company(
            id=2,
            ticker_symbol="9984",
            company_name_jp="ソフトバンクグループ",
            company_name_en="SoftBank Group Corp.",
            market_division="Prime",
            industry_name="情報・通信業",
            market_cap=8000000,  # 8兆円
            employee_count=50000
        ),
        Company(
            id=3,
            ticker_symbol="6758",
            company_name_jp="ソニーグループ",
            company_name_en="Sony Group Corporation",
            market_division="Prime",
            industry_name="電気機器",
            market_cap=12000000,  # 12兆円
            employee_count=110000
        )
    ]
    
    for company in companies:
        db_session.add(company)
    
    # Add sample financial indicators
    indicators = [
        FinancialIndicator(
            company_id=1,
            roe=8.5,
            roa=4.2,
            operating_margin=9.1,
            equity_ratio=45.2,
            current_ratio=105.3,
            per=12.5,
            pbr=1.1,
            dividend_yield=2.8
        ),
        FinancialIndicator(
            company_id=2,
            roe=12.3,
            roa=3.8,
            operating_margin=15.2,
            equity_ratio=25.1,
            current_ratio=98.7,
            per=18.9,
            pbr=2.3,
            dividend_yield=0.8
        ),
        FinancialIndicator(
            company_id=3,
            roe=15.7,
            roa=6.9,
            operating_margin=12.8,
            equity_ratio=55.8,
            current_ratio=142.1,
            per=14.2,
            pbr=1.8,
            dividend_yield=1.2
        )
    ]
    
    for indicator in indicators:
        db_session.add(indicator)
    
    db_session.commit()
    return companies


class TestCompaniesAPI:
    """Test cases for companies API endpoints"""

    def test_get_companies_list(self, client, setup_database, sample_companies):
        """Test getting companies list"""
        response = client.get("/api/v1/companies/")
        assert response.status_code == 200
        
        data = response.json()
        assert "companies" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["companies"]) == 3

    def test_get_companies_with_search(self, client, setup_database, sample_companies):
        """Test companies search functionality"""
        response = client.get("/api/v1/companies/?q=トヨタ")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 1
        assert data["companies"][0]["company_name_jp"] == "トヨタ自動車"

    def test_get_companies_with_market_filter(self, client, setup_database, sample_companies):
        """Test companies filtering by market division"""
        response = client.get("/api/v1/companies/?market_division=Prime")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 3  # All sample companies are Prime

    def test_get_companies_pagination(self, client, setup_database, sample_companies):
        """Test companies pagination"""
        response = client.get("/api/v1/companies/?page=1&size=2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["companies"]) == 2
        assert data["page"] == 1
        assert data["size"] == 2
        assert data["total_pages"] == 2

    def test_get_company_by_id(self, client, setup_database, sample_companies):
        """Test getting individual company"""
        response = client.get("/api/v1/companies/1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["ticker_symbol"] == "7203"
        assert data["company_name_jp"] == "トヨタ自動車"

    def test_get_company_not_found(self, client, setup_database):
        """Test getting non-existent company"""
        response = client.get("/api/v1/companies/999")
        assert response.status_code == 404

    def test_get_company_financials(self, client, setup_database, sample_companies):
        """Test getting company financial statements"""
        response = client.get("/api/v1/companies/1/financials")
        assert response.status_code == 200
        
        data = response.json()
        assert data["company_id"] == 1
        assert "financial_statements" in data

    def test_get_company_indicators(self, client, setup_database, sample_companies):
        """Test getting company financial indicators"""
        response = client.get("/api/v1/companies/1/indicators")
        assert response.status_code == 200
        
        data = response.json()
        assert data["company_id"] == 1
        assert "indicators" in data
        assert "profitability" in data["indicators"]
        assert "safety" in data["indicators"]
        assert data["indicators"]["profitability"]["roe"] == 8.5

    def test_create_company(self, client, setup_database):
        """Test creating new company"""
        company_data = {
            "ticker_symbol": "1234",
            "company_name_jp": "テスト会社",
            "market_division": "Standard",
            "industry_name": "サービス業"
        }
        
        response = client.post("/api/v1/companies/", json=company_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["ticker_symbol"] == "1234"
        assert data["company_name_jp"] == "テスト会社"

    def test_create_company_duplicate_ticker(self, client, setup_database, sample_companies):
        """Test creating company with duplicate ticker"""
        company_data = {
            "ticker_symbol": "7203",  # Already exists
            "company_name_jp": "重複会社",
        }
        
        response = client.post("/api/v1/companies/", json=company_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_update_company(self, client, setup_database, sample_companies):
        """Test updating company information"""
        update_data = {
            "company_name_jp": "トヨタ自動車株式会社（更新）",
            "employee_count": 75000
        }
        
        response = client.put("/api/v1/companies/1", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["company_name_jp"] == "トヨタ自動車株式会社（更新）"
        assert data["employee_count"] == 75000

    def test_delete_company(self, client, setup_database, sample_companies):
        """Test deleting company"""
        response = client.delete("/api/v1/companies/1")
        assert response.status_code == 204
        
        # Verify company is deleted
        get_response = client.get("/api/v1/companies/1")
        assert get_response.status_code == 404