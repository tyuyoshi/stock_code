"""Test cases for screening API endpoints"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.main import app
from core.database import get_db, Base
from models.company import Company
from models.financial import FinancialIndicator

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_screening.db"
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
def sample_screening_data(db_session):
    """Create sample data for screening tests"""
    companies = [
        Company(
            id=1,
            ticker_symbol="7203",
            company_name_jp="トヨタ自動車",
            market_division="Prime",
            industry_name="輸送用機器",
            market_cap=35000000
        ),
        Company(
            id=2,
            ticker_symbol="9984",
            company_name_jp="ソフトバンクグループ",
            market_division="Prime",
            industry_name="情報・通信業",
            market_cap=8000000
        ),
        Company(
            id=3,
            ticker_symbol="8306",
            company_name_jp="三菱UFJフィナンシャル・グループ",
            market_division="Prime",
            industry_name="銀行業",
            market_cap=10000000
        ),
        Company(
            id=4,
            ticker_symbol="4005",
            company_name_jp="住友化学",
            market_division="Standard",
            industry_name="化学",
            market_cap=2000000
        )
    ]
    
    for company in companies:
        db_session.add(company)
    
    # Add financial indicators with varying values for testing
    indicators = [
        FinancialIndicator(
            company_id=1,
            roe=8.5,  # Low ROE
            per=12.5,  # Reasonable PER
            dividend_yield=2.8,
            equity_ratio=45.2,
            current_ratio=105.3
        ),
        FinancialIndicator(
            company_id=2,
            roe=18.9,  # High ROE
            per=25.3,  # High PER
            dividend_yield=0.8,  # Low dividend
            equity_ratio=25.1,
            current_ratio=98.7
        ),
        FinancialIndicator(
            company_id=3,
            roe=12.1,  # Medium ROE
            per=8.9,   # Low PER
            dividend_yield=4.2,  # High dividend
            equity_ratio=15.8,
            current_ratio=88.2
        ),
        FinancialIndicator(
            company_id=4,
            roe=22.3,  # Very high ROE
            per=15.7,  # Medium PER
            dividend_yield=1.5,
            equity_ratio=65.4,  # High equity ratio
            current_ratio=155.8  # High current ratio
        )
    ]
    
    for indicator in indicators:
        db_session.add(indicator)
    
    db_session.commit()
    return companies


class TestScreeningAPI:
    """Test cases for screening API endpoints"""

    def test_execute_screening_high_roe(self, client, setup_database, sample_screening_data):
        """Test screening for high ROE companies"""
        screening_request = {
            "filters": [
                {
                    "field": "roe",
                    "operator": "gte",
                    "value": 15.0
                }
            ],
            "page": 1,
            "size": 10,
            "include_indicators": True
        }
        
        response = client.post("/api/v1/screening/", json=screening_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert data["total"] == 2  # Companies 2 and 4 have ROE >= 15%
        assert len(data["results"]) == 2
        
        # Check that indicators are included
        assert data["results"][0]["indicators"] is not None

    def test_execute_screening_low_per(self, client, setup_database, sample_screening_data):
        """Test screening for low PER companies"""
        screening_request = {
            "filters": [
                {
                    "field": "per",
                    "operator": "lte",
                    "value": 15.0
                }
            ],
            "sort": {
                "field": "per",
                "order": "asc"
            }
        }
        
        response = client.post("/api/v1/screening/", json=screening_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 3  # Companies 1, 3, 4 have PER <= 15
        
        # Check sorting - first result should have lowest PER
        first_result = data["results"][0]
        assert first_result["ticker_symbol"] == "8306"  # Company 3 has PER 8.9

    def test_execute_screening_multiple_filters(self, client, setup_database, sample_screening_data):
        """Test screening with multiple filters"""
        screening_request = {
            "filters": [
                {
                    "field": "roe",
                    "operator": "gte",
                    "value": 10.0
                },
                {
                    "field": "equity_ratio",
                    "operator": "gte",
                    "value": 40.0
                }
            ]
        }
        
        response = client.post("/api/v1/screening/", json=screening_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 2  # Only companies 1 and 4 meet both criteria

    def test_execute_screening_market_division_filter(self, client, setup_database, sample_screening_data):
        """Test screening by market division"""
        screening_request = {
            "filters": [
                {
                    "field": "market_division",
                    "operator": "eq",
                    "value": "Prime"
                }
            ]
        }
        
        response = client.post("/api/v1/screening/", json=screening_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 3  # Companies 1, 2, 3 are Prime

    def test_execute_screening_pagination(self, client, setup_database, sample_screening_data):
        """Test screening pagination"""
        screening_request = {
            "filters": [
                {
                    "field": "market_division",
                    "operator": "eq",
                    "value": "Prime"
                }
            ],
            "page": 1,
            "size": 2
        }
        
        response = client.post("/api/v1/screening/", json=screening_request)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["results"]) == 2
        assert data["page"] == 1
        assert data["size"] == 2
        assert data["total_pages"] == 2

    def test_execute_screening_invalid_field(self, client, setup_database, sample_screening_data):
        """Test screening with invalid field"""
        screening_request = {
            "filters": [
                {
                    "field": "invalid_field",
                    "operator": "gte",
                    "value": 10.0
                }
            ]
        }
        
        response = client.post("/api/v1/screening/", json=screening_request)
        assert response.status_code == 400
        assert "Invalid filter field" in response.json()["detail"]

    def test_get_screening_presets(self, client, setup_database):
        """Test getting screening presets"""
        response = client.get("/api/v1/screening/presets")
        assert response.status_code == 200
        
        data = response.json()
        assert "presets" in data
        assert "categories" in data
        assert len(data["presets"]) > 0
        
        # Check for expected presets
        preset_ids = [preset["id"] for preset in data["presets"]]
        assert "high_roe" in preset_ids
        assert "low_per" in preset_ids
        assert "high_dividend" in preset_ids

    def test_execute_preset_screening(self, client, setup_database, sample_screening_data):
        """Test executing preset screening"""
        response = client.get("/api/v1/screening/presets/high_roe?page=1&size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert data["total"] == 2  # Companies with ROE >= 15%

    def test_execute_preset_screening_not_found(self, client, setup_database):
        """Test executing non-existent preset"""
        response = client.get("/api/v1/screening/presets/invalid_preset")
        assert response.status_code == 404

    def test_get_screening_fields(self, client, setup_database):
        """Test getting available screening fields"""
        response = client.get("/api/v1/screening/fields")
        assert response.status_code == 200
        
        data = response.json()
        assert "fields" in data
        assert "categories" in data
        assert len(data["fields"]) > 0
        
        # Check for expected field categories
        categories = data["categories"]
        assert "profitability" in categories
        assert "safety" in categories
        assert "valuation" in categories
        
        # Check field structure
        first_field = data["fields"][0]
        assert "field" in first_field
        assert "label" in first_field
        assert "data_type" in first_field
        assert "category" in first_field