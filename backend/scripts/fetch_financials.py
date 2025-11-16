"""
Fetch and load financial statement data.

This script fetches financial data for companies from EDINET API or CSV file
and loads it into the database. It processes multiple quarters of data per company.
"""

import argparse
import logging
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import SessionLocal
from models.company import Company
from models.financial import FinancialStatement
from services.edinet_client import EDINETClient
from services.xbrl_parser import XBRLParser
from services.data_processor import DataProcessor
from scripts.utils import (
    DataLoadError,
    ProgressTracker,
    get_db_session,
    log_data_quality_report,
    logger,
    retry_on_error,
    safe_float,
    safe_int,
    validate_required_fields,
)

logger = logging.getLogger(__name__)


def load_financials_from_csv(csv_path: str) -> List[Dict]:
    """
    Load financial data from CSV file.

    CSV should have columns:
    - ticker_symbol (required)
    - fiscal_year (required)
    - fiscal_quarter (1-4, or NULL for annual)
    - period_end (required, YYYY-MM-DD format)
    - period_start (optional)
    - revenue
    - cost_of_revenue
    - gross_profit
    - operating_expenses
    - operating_income
    - net_income
    - total_assets
    - current_assets
    - total_liabilities
    - current_liabilities
    - shareholders_equity
    - operating_cash_flow
    - investing_cash_flow
    - financing_cash_flow
    - free_cash_flow

    Args:
        csv_path: Path to CSV file

    Returns:
        List of financial statement dictionaries

    Raises:
        DataLoadError: If CSV file cannot be read
    """
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} financial records from {csv_path}")

        financials = []
        for _, row in df.iterrows():
            financial_data = {
                "ticker_symbol": str(row.get("ticker_symbol", "")).strip(),
                "fiscal_year": safe_int(row.get("fiscal_year")),
                "fiscal_quarter": safe_int(row.get("fiscal_quarter"))
                if pd.notna(row.get("fiscal_quarter"))
                else None,
                "period_end": pd.to_datetime(row.get("period_end")).date()
                if pd.notna(row.get("period_end"))
                else None,
                "period_start": pd.to_datetime(row.get("period_start")).date()
                if pd.notna(row.get("period_start"))
                else None,
                "is_consolidated": bool(row.get("is_consolidated", True)),
                # Income Statement
                "revenue": safe_float(row.get("revenue")),
                "cost_of_revenue": safe_float(row.get("cost_of_revenue")),
                "gross_profit": safe_float(row.get("gross_profit")),
                "operating_expenses": safe_float(row.get("operating_expenses")),
                "operating_income": safe_float(row.get("operating_income")),
                "net_income": safe_float(row.get("net_income")),
                # Balance Sheet
                "total_assets": safe_float(row.get("total_assets")),
                "current_assets": safe_float(row.get("current_assets")),
                "total_liabilities": safe_float(row.get("total_liabilities")),
                "current_liabilities": safe_float(row.get("current_liabilities")),
                "shareholders_equity": safe_float(row.get("shareholders_equity")),
                # Cash Flow
                "operating_cash_flow": safe_float(row.get("operating_cash_flow")),
                "investing_cash_flow": safe_float(row.get("investing_cash_flow")),
                "financing_cash_flow": safe_float(row.get("financing_cash_flow")),
                "free_cash_flow": safe_float(row.get("free_cash_flow")),
            }

            financials.append(financial_data)

        return financials

    except FileNotFoundError:
        raise DataLoadError(f"CSV file not found: {csv_path}")
    except Exception as e:
        raise DataLoadError(f"Failed to load CSV: {str(e)}")


def fetch_from_edinet(
    company: Company, num_quarters: int = 8
) -> List[Dict]:
    """
    Fetch financial data from EDINET API for a company.

    This is a placeholder for EDINET integration. In production, this would:
    1. Search for company's financial reports
    2. Download XBRL documents
    3. Parse financial data
    4. Return structured data

    Args:
        company: Company model instance
        num_quarters: Number of quarters to fetch

    Returns:
        List of financial statement dictionaries
    """
    # This is a placeholder - actual EDINET integration would be more complex
    logger.warning(
        f"EDINET integration not yet implemented for {company.ticker_symbol}. "
        "Use CSV import for now."
    )
    return []


def validate_financial_data(financial: Dict) -> bool:
    """
    Validate financial data has required fields.

    Args:
        financial: Financial dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["ticker_symbol", "fiscal_year", "period_end"]
    return validate_required_fields(financial, required_fields)


def insert_financials(
    session: Session, financials: List[Dict]
) -> Dict[str, int]:
    """
    Insert financial statements into database.

    Args:
        session: SQLAlchemy session
        financials: List of financial statement dictionaries

    Returns:
        Dictionary with statistics (success, errors, duplicates, validation_failures)
    """
    stats = {
        "success": 0,
        "errors": 0,
        "duplicates": 0,
        "validation_failures": 0,
    }

    progress = ProgressTracker(len(financials), "Inserting financial statements")

    for financial in financials:
        try:
            # Validate data
            if not validate_financial_data(financial):
                stats["validation_failures"] += 1
                progress.update(1, success=False)
                continue

            # Get company by ticker symbol
            ticker = financial.pop("ticker_symbol")
            company = session.query(Company).filter(
                Company.ticker_symbol == ticker
            ).first()

            if not company:
                logger.warning(f"Company not found: {ticker}")
                stats["errors"] += 1
                progress.update(1, success=False)
                continue

            # Add company_id to financial data
            financial["company_id"] = company.id

            # Check for duplicate (same company, fiscal_year, fiscal_quarter)
            existing = session.query(FinancialStatement).filter(
                FinancialStatement.company_id == company.id,
                FinancialStatement.fiscal_year == financial["fiscal_year"],
                FinancialStatement.fiscal_quarter == financial.get("fiscal_quarter"),
            ).first()

            if existing:
                logger.debug(
                    f"Skipping duplicate financial record: {ticker} "
                    f"FY{financial['fiscal_year']} Q{financial.get('fiscal_quarter', 'Annual')}"
                )
                stats["duplicates"] += 1
                progress.update(1, success=True)
                continue

            # Insert financial statement
            db_financial = FinancialStatement(**financial)
            session.add(db_financial)
            session.commit()

            stats["success"] += 1
            progress.update(1, success=True)

        except IntegrityError as e:
            session.rollback()
            logger.warning(f"Integrity error: {str(e)}")
            stats["duplicates"] += 1
            progress.update(1, success=True)

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to insert financial data: {str(e)}")
            stats["errors"] += 1
            progress.update(1, success=False)

    progress.close()
    return stats


def generate_sample_csv(
    output_path: str = "financials_sample.csv", num_samples: int = 20
):
    """
    Generate a sample CSV file with example financial data.

    Args:
        output_path: Path to output CSV file
        num_samples: Number of sample financial records to generate
    """
    sample_data = []

    # Generate 4 quarters for 5 companies
    quarter_ends = ["03-31", "06-30", "09-30", "12-31"]
    quarter_starts = ["01-01", "04-01", "07-01", "10-01"]

    for company_idx in range(5):
        ticker = f"{7200 + company_idx}"
        for quarter in range(4):
            sample_data.append(
                {
                    "ticker_symbol": ticker,
                    "fiscal_year": 2024,
                    "fiscal_quarter": quarter + 1,
                    "period_start": f"2024-{quarter_starts[quarter]}",
                    "period_end": f"2024-{quarter_ends[quarter]}",
                    "is_consolidated": True,
                    "revenue": 100000000.0 * (quarter + 1),
                    "cost_of_revenue": 60000000.0 * (quarter + 1),
                    "gross_profit": 40000000.0 * (quarter + 1),
                    "operating_expenses": 20000000.0 * (quarter + 1),
                    "operating_income": 20000000.0 * (quarter + 1),
                    "net_income": 15000000.0 * (quarter + 1),
                    "total_assets": 500000000.0,
                    "current_assets": 200000000.0,
                    "total_liabilities": 300000000.0,
                    "current_liabilities": 100000000.0,
                    "shareholders_equity": 200000000.0,
                    "operating_cash_flow": 18000000.0 * (quarter + 1),
                    "investing_cash_flow": -5000000.0 * (quarter + 1),
                    "financing_cash_flow": -3000000.0 * (quarter + 1),
                    "free_cash_flow": 13000000.0 * (quarter + 1),
                }
            )

    df = pd.DataFrame(sample_data)
    df.to_csv(output_path, index=False)
    logger.info(f"Generated sample CSV with {len(sample_data)} financial records at {output_path}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Fetch and load financial statement data"
    )
    parser.add_argument(
        "--csv",
        type=str,
        help="Path to CSV file containing financial data",
    )
    parser.add_argument(
        "--generate-sample",
        action="store_true",
        help="Generate a sample CSV file for testing",
    )
    parser.add_argument(
        "--edinet",
        action="store_true",
        help="Fetch data from EDINET API (requires EDINET_API_KEY)",
    )
    parser.add_argument(
        "--quarters",
        type=int,
        default=8,
        help="Number of quarters to fetch per company (default: 8)",
    )

    args = parser.parse_args()

    try:
        # Generate sample CSV if requested
        if args.generate_sample:
            generate_sample_csv("financials_sample.csv")
            logger.info("Sample CSV generation complete")
            return 0

        # Load from CSV
        if args.csv:
            logger.info(f"Loading financial data from: {args.csv}")
            financials = load_financials_from_csv(args.csv)
        elif args.edinet:
            logger.error("EDINET API integration not yet implemented. Use --csv instead.")
            return 1
        else:
            logger.error("Please provide --csv argument or use --generate-sample")
            parser.print_help()
            return 1

        if not financials:
            logger.warning("No financial data to insert")
            return 1

        logger.info(f"Loaded {len(financials)} financial records, starting insertion...")

        # Insert financial data
        with get_db_session() as session:
            stats = insert_financials(session, financials)

        # Log summary
        log_data_quality_report(
            total=len(financials),
            success=stats["success"],
            errors=stats["errors"],
            duplicates=stats["duplicates"],
            validation_failures=stats["validation_failures"],
        )

        if stats["errors"] > 0:
            logger.warning(f"Completed with {stats['errors']} errors")
            return 1

        logger.info("Financial data loading completed successfully!")
        return 0

    except DataLoadError as e:
        logger.error(f"Data load error: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
