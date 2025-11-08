"""Test cases for export API endpoints"""

import pytest
import io
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime, timedelta

# Disable rate limiting for tests
os.environ["ENVIRONMENT"] = "development"

from api.main import app
from core.database import get_db, Base
from models.company import Company
from models.financial import FinancialIndicator, FinancialStatement, StockPrice

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_export.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
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
def sample_export_data(db_session, setup_database):
    """Create sample data for export tests"""
    # Clear existing data
    db_session.query(StockPrice).delete()
    db_session.query(FinancialIndicator).delete()
    db_session.query(FinancialStatement).delete()
    db_session.query(Company).delete()
    db_session.commit()

    companies = [
        Company(
            id=1,
            ticker_symbol="7203",
            company_name_jp="トヨタ自動車",
            company_name_en="Toyota Motor Corporation",
            market_division="Prime",
            industry_name="輸送用機器",
            market_cap=35000000,
            employee_count=70000,
        ),
        Company(
            id=2,
            ticker_symbol="9984",
            company_name_jp="ソフトバンクグループ",
            company_name_en="SoftBank Group Corp.",
            market_division="Prime",
            industry_name="情報・通信業",
            market_cap=8000000,
            employee_count=50000,
        ),
        Company(
            id=3,
            ticker_symbol="6758",
            company_name_jp="ソニーグループ",
            company_name_en="Sony Group Corporation",
            market_division="Prime",
            industry_name="電気機器",
            market_cap=12000000,
            employee_count=40000,
        ),
    ]

    for company in companies:
        db_session.add(company)

    db_session.commit()

    # Add financial indicators
    today = date.today()
    indicators = [
        FinancialIndicator(
            company_id=1,
            date=today,
            roe=18.5,
            roa=8.2,
            operating_margin=12.5,
            per=11.2,
            pbr=1.3,
            dividend_yield=2.8,
        ),
        FinancialIndicator(
            company_id=2,
            date=today,
            roe=12.3,
            roa=5.1,
            operating_margin=15.2,
            per=9.8,
            pbr=1.1,
            dividend_yield=5.2,
        ),
        FinancialIndicator(
            company_id=3,
            date=today,
            roe=15.7,
            roa=6.9,
            operating_margin=13.8,
            per=15.3,
            pbr=2.1,
            dividend_yield=0.5,
        ),
    ]

    for indicator in indicators:
        db_session.add(indicator)

    # Add financial statements
    statements = [
        FinancialStatement(
            company_id=1,
            fiscal_year=2024,
            period_end=date(2024, 3, 31),
            revenue=37154200,
            operating_income=4646500,
            net_income=2893300,
            total_assets=71634400,
            shareholders_equity=32306700,
        ),
        FinancialStatement(
            company_id=2,
            fiscal_year=2024,
            period_end=date(2024, 3, 31),
            revenue=5400000,
            operating_income=820000,
            net_income=490000,
            total_assets=48000000,
            shareholders_equity=8500000,
        ),
    ]

    for stmt in statements:
        db_session.add(stmt)

    # Add stock prices
    for company_id in [1, 2, 3]:
        for i in range(5):
            price_date = today - timedelta(days=i)
            stock_price = StockPrice(
                company_id=company_id,
                date=price_date,
                open_price=2000 + i * 10,
                high_price=2050 + i * 10,
                low_price=1980 + i * 10,
                close_price=2020 + i * 10,
                volume=1000000 + i * 10000,
            )
            db_session.add(stock_price)

    db_session.commit()

    yield companies


class TestScreeningExport:
    """Test screening results export functionality"""

    def test_export_screening_csv_success(
        self, client, setup_database, sample_export_data
    ):
        """Test successful CSV export of screening results"""
        response = client.post(
            "/api/v1/export/screening",
            json={
                "data_type": "screening_results",
                "format": "csv",
                "filters": [{"field": "roe", "operator": "gte", "value": 15.0}],
                "include_indicators": True,
                "max_rows": 100,
                "filename": "test_screening",
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "test_screening.csv" in response.headers["content-disposition"]

        content = response.content.decode("utf-8-sig")
        assert "ティッカー" in content or "ticker" in content.lower()
        assert "7203" in content or "6758" in content

    def test_export_screening_excel_success(
        self, client, setup_database, sample_export_data
    ):
        """Test successful Excel export of screening results"""
        response = client.post(
            "/api/v1/export/screening",
            json={
                "data_type": "screening_results",
                "format": "excel",
                "filters": [
                    {"field": "market_division", "operator": "eq", "value": "Prime"}
                ],
                "include_indicators": True,
                "max_rows": 50,
            },
        )

        assert response.status_code == 200
        assert "spreadsheet" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]

    def test_export_screening_max_rows_limit(
        self, client, setup_database, sample_export_data
    ):
        """Test max_rows limit enforcement"""
        response = client.post(
            "/api/v1/export/screening",
            json={
                "data_type": "screening_results",
                "format": "csv",
                "filters": [],
                "max_rows": 2,
            },
        )

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        lines = [
            line for line in content.split("\n") if line and not line.startswith("#")
        ]
        assert len(lines) <= 3


class TestComparisonExport:
    """Test company comparison export functionality"""

    def test_export_comparison_excel_success(
        self, client, setup_database, sample_export_data
    ):
        """Test successful Excel export of comparison results"""
        response = client.post(
            "/api/v1/export/comparison",
            json={
                "data_type": "comparison",
                "format": "excel",
                "company_ids": [1, 2, 3],
                "metrics": ["roe", "roa", "per", "pbr"],
                "include_rankings": True,
                "filename": "test_comparison",
            },
        )

        assert response.status_code == 200
        assert "spreadsheet" in response.headers["content-type"]
        assert "test_comparison.xlsx" in response.headers["content-disposition"]

    def test_export_comparison_invalid_companies(
        self, client, setup_database, sample_export_data
    ):
        """Test export with invalid company IDs"""
        response = client.post(
            "/api/v1/export/comparison",
            json={
                "data_type": "comparison",
                "format": "excel",
                "company_ids": [999, 1000],
                "include_rankings": False,
            },
        )

        assert response.status_code in [400, 404, 500]

    def test_export_comparison_csv_not_supported(
        self, client, setup_database, sample_export_data
    ):
        """Test that CSV format is not supported for comparison"""
        response = client.post(
            "/api/v1/export/comparison",
            json={"data_type": "comparison", "format": "csv", "company_ids": [1, 2]},
        )

        assert response.status_code == 400
        assert (
            "Excel" in response.json()["detail"]
            or "excel" in response.json()["detail"].lower()
        )


class TestFinancialDataExport:
    """Test financial data export functionality"""

    def test_export_financial_data_success(
        self, client, setup_database, sample_export_data
    ):
        """Test successful financial data export"""
        response = client.post(
            "/api/v1/export/financial-data",
            json={
                "data_type": "financial_data",
                "format": "excel",
                "company_ids": [1, 2],
                "data_types": ["statements", "indicators"],
                "periods": 5,
                "filename": "test_financial",
            },
        )

        assert response.status_code == 200
        assert "spreadsheet" in response.headers["content-type"]
        assert "test_financial.xlsx" in response.headers["content-disposition"]

    def test_export_financial_data_stock_prices(
        self, client, setup_database, sample_export_data
    ):
        """Test financial data export including stock prices"""
        response = client.post(
            "/api/v1/export/financial-data",
            json={
                "data_type": "financial_data",
                "format": "excel",
                "company_ids": [1],
                "data_types": ["stock_prices"],
                "periods": 3,
            },
        )

        assert response.status_code == 200
        assert "spreadsheet" in response.headers["content-type"]

    def test_export_financial_data_invalid_company(
        self, client, setup_database, sample_export_data
    ):
        """Test export with non-existent company"""
        response = client.post(
            "/api/v1/export/financial-data",
            json={
                "data_type": "financial_data",
                "format": "excel",
                "company_ids": [9999],
                "data_types": ["statements"],
            },
        )

        assert response.status_code in [404, 500]

    def test_export_financial_data_csv_not_supported(
        self, client, setup_database, sample_export_data
    ):
        """Test that CSV format is not supported for financial data"""
        response = client.post(
            "/api/v1/export/financial-data",
            json={
                "data_type": "financial_data",
                "format": "csv",
                "company_ids": [1],
                "data_types": ["statements"],
            },
        )

        assert response.status_code == 400


class TestExportIntegration:
    """Integration tests for export endpoints"""

    def test_export_templates_endpoint(self, client, setup_database):
        """Test export templates endpoint"""
        response = client.get("/api/v1/export/templates")

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "categories" in data
        assert len(data["templates"]) > 0

    def test_export_formats_endpoint(self, client, setup_database):
        """Test export formats endpoint"""
        response = client.get("/api/v1/export/formats")

        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert len(data["formats"]) >= 2

        formats = {f["format"] for f in data["formats"]}
        assert "csv" in formats
        assert "excel" in formats
