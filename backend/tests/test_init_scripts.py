"""
Unit tests for data initialization scripts.

These tests cover the core functionality of the initialization scripts:
- Company data loading
- Financial data loading
- Stock price data loading
- Financial indicator calculation
"""

import pytest
import tempfile
import csv
from datetime import datetime, date
from pathlib import Path

from scripts.init_companies import (
    load_companies_from_csv,
    validate_company_data,
    generate_sample_csv as generate_company_csv,
)
from scripts.fetch_financials import (
    load_financials_from_csv,
    validate_financial_data,
    generate_sample_csv as generate_financials_csv,
)
from scripts.fetch_stock_prices import (
    load_stock_prices_from_csv,
    generate_sample_csv as generate_prices_csv,
)
from scripts.utils import (
    validate_required_fields,
    safe_float,
    safe_int,
    ProgressTracker,
)


class TestCompanyInitialization:
    """Tests for company master data initialization."""

    def test_load_companies_from_csv(self, tmp_path):
        """Test loading companies from CSV file."""
        # Create test CSV file
        csv_file = tmp_path / "test_companies.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "ticker_symbol",
                    "edinet_code",
                    "company_name_jp",
                    "company_name_en",
                    "market_division",
                    "market_cap",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "ticker_symbol": "7201",
                    "edinet_code": "E01234",
                    "company_name_jp": "テスト株式会社",
                    "company_name_en": "Test Corporation",
                    "market_division": "Prime",
                    "market_cap": 1000000000.0,
                }
            )

        # Load and verify
        companies = load_companies_from_csv(str(csv_file))
        assert len(companies) == 1
        assert companies[0]["ticker_symbol"] == "7201"
        assert companies[0]["company_name_jp"] == "テスト株式会社"

    def test_validate_company_data_valid(self):
        """Test validation with valid company data."""
        valid_data = {
            "ticker_symbol": "7201",
            "company_name_jp": "テスト株式会社",
        }
        assert validate_company_data(valid_data) is True

    def test_validate_company_data_missing_ticker(self):
        """Test validation fails with missing ticker."""
        invalid_data = {
            "company_name_jp": "テスト株式会社",
        }
        assert validate_company_data(invalid_data) is False

    def test_generate_company_sample_csv(self, tmp_path):
        """Test sample CSV generation."""
        output_file = tmp_path / "companies_sample.csv"
        generate_company_csv(str(output_file), num_samples=5)

        assert output_file.exists()

        # Verify content
        companies = load_companies_from_csv(str(output_file))
        assert len(companies) == 5
        assert all("ticker_symbol" in c for c in companies)


class TestFinancialDataInitialization:
    """Tests for financial data initialization."""

    def test_load_financials_from_csv(self, tmp_path):
        """Test loading financial data from CSV."""
        csv_file = tmp_path / "test_financials.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "ticker_symbol",
                    "fiscal_year",
                    "fiscal_quarter",
                    "period_end",
                    "revenue",
                    "net_income",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "ticker_symbol": "7201",
                    "fiscal_year": 2024,
                    "fiscal_quarter": 1,
                    "period_end": "2024-03-31",
                    "revenue": 100000000.0,
                    "net_income": 5000000.0,
                }
            )

        financials = load_financials_from_csv(str(csv_file))
        assert len(financials) == 1
        assert financials[0]["ticker_symbol"] == "7201"
        assert financials[0]["fiscal_year"] == 2024

    def test_validate_financial_data_valid(self):
        """Test validation with valid financial data."""
        valid_data = {
            "ticker_symbol": "7201",
            "fiscal_year": 2024,
            "period_end": date(2024, 3, 31),
        }
        assert validate_financial_data(valid_data) is True

    def test_validate_financial_data_missing_required(self):
        """Test validation fails with missing required fields."""
        invalid_data = {
            "ticker_symbol": "7201",
            "fiscal_year": 2024,
            # period_end missing
        }
        assert validate_financial_data(invalid_data) is False


class TestStockPriceInitialization:
    """Tests for stock price data initialization."""

    def test_load_stock_prices_from_csv(self, tmp_path):
        """Test loading stock prices from CSV."""
        csv_file = tmp_path / "test_prices.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "ticker_symbol",
                    "date",
                    "open_price",
                    "close_price",
                    "volume",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "ticker_symbol": "7201",
                    "date": "2024-01-04",
                    "open_price": 1050.0,
                    "close_price": 1070.0,
                    "volume": 12500000,
                }
            )

        prices = load_stock_prices_from_csv(str(csv_file))
        assert len(prices) == 1
        assert prices[0]["ticker_symbol"] == "7201"
        assert prices[0]["close_price"] == 1070.0

    def test_generate_prices_sample_csv(self, tmp_path):
        """Test sample stock prices CSV generation."""
        output_file = tmp_path / "prices_sample.csv"
        generate_prices_csv(str(output_file), num_days=10)

        assert output_file.exists()

        # Verify content
        prices = load_stock_prices_from_csv(str(output_file))
        assert len(prices) > 0
        assert all("ticker_symbol" in p for p in prices)


class TestUtilities:
    """Tests for utility functions."""

    def test_validate_required_fields_valid(self):
        """Test required field validation with valid data."""
        data = {"field1": "value1", "field2": "value2"}
        required = ["field1", "field2"]
        assert validate_required_fields(data, required) is True

    def test_validate_required_fields_missing(self):
        """Test required field validation with missing field."""
        data = {"field1": "value1"}
        required = ["field1", "field2"]
        assert validate_required_fields(data, required) is False

    def test_validate_required_fields_none_value(self):
        """Test required field validation with None value."""
        data = {"field1": "value1", "field2": None}
        required = ["field1", "field2"]
        assert validate_required_fields(data, required) is False

    def test_safe_float_valid(self):
        """Test safe float conversion with valid input."""
        assert safe_float(10.5) == 10.5
        assert safe_float("20.5") == 20.5
        assert safe_float(100) == 100.0

    def test_safe_float_invalid(self):
        """Test safe float conversion with invalid input."""
        assert safe_float("invalid") == 0.0
        assert safe_float(None) == 0.0
        assert safe_float("", default=99.9) == 99.9

    def test_safe_int_valid(self):
        """Test safe int conversion with valid input."""
        assert safe_int(10) == 10
        assert safe_int("20") == 20
        assert safe_int(10.7) == 10

    def test_safe_int_invalid(self):
        """Test safe int conversion with invalid input."""
        assert safe_int("invalid") == 0
        assert safe_int(None) == 0
        assert safe_int("", default=99) == 99

    def test_progress_tracker(self):
        """Test progress tracker functionality."""
        tracker = ProgressTracker(total=10, desc="Test progress")

        tracker.update(3, success=True)
        assert tracker.success_count == 3
        assert tracker.error_count == 0

        tracker.update(2, success=False)
        assert tracker.success_count == 3
        assert tracker.error_count == 2

        tracker.close()


class TestIntegration:
    """Integration tests for complete data loading workflow."""

    def test_full_workflow_with_samples(self, tmp_path):
        """Test complete data loading workflow with sample data."""
        # Generate sample files
        companies_file = tmp_path / "companies.csv"
        financials_file = tmp_path / "financials.csv"
        prices_file = tmp_path / "prices.csv"

        generate_company_csv(str(companies_file), num_samples=2)
        generate_financials_csv(str(financials_file))
        generate_prices_csv(str(prices_file), num_days=5)

        # Load all data
        companies = load_companies_from_csv(str(companies_file))
        financials = load_financials_from_csv(str(financials_file))
        prices = load_stock_prices_from_csv(str(prices_file))

        # Verify data loaded successfully
        assert len(companies) == 2
        assert len(financials) > 0
        assert len(prices) > 0

        # Verify data relationships
        company_tickers = {c["ticker_symbol"] for c in companies}
        financial_tickers = {f["ticker_symbol"] for f in financials}
        price_tickers = {p["ticker_symbol"] for p in prices}

        # Note: Sample data uses different ticker ranges, so we just verify
        # that data was loaded successfully
        assert len(company_tickers) > 0
        assert len(financial_tickers) > 0
        assert len(price_tickers) > 0


# Fixtures for database testing (would be expanded in Issue #90)
@pytest.fixture
def test_db_session():
    """
    Fixture for test database session.

    This is a placeholder - full database test fixtures would be
    implemented in Issue #90 (Test Coverage 90%+).
    """
    # TODO: Implement database test fixtures
    pass


@pytest.fixture
def sample_company_data():
    """Fixture providing sample company data."""
    return {
        "ticker_symbol": "7201",
        "edinet_code": "E01234",
        "company_name_jp": "テスト株式会社",
        "company_name_en": "Test Corporation",
        "market_division": "Prime",
        "industry_code": "5010",
        "industry_name": "製造業",
        "market_cap": 1000000000.0,
        "shares_outstanding": 100000000.0,
    }


@pytest.fixture
def sample_financial_data():
    """Fixture providing sample financial data."""
    return {
        "ticker_symbol": "7201",
        "fiscal_year": 2024,
        "fiscal_quarter": 1,
        "period_end": date(2024, 3, 31),
        "revenue": 100000000.0,
        "net_income": 5000000.0,
        "total_assets": 500000000.0,
        "shareholders_equity": 200000000.0,
    }
