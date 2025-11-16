"""
Initialize company master data.

This script loads initial company data into the database. It supports loading from:
1. CSV file with company information
2. EDINET API (for specific companies)
3. Manual data input

The script validates data, checks for duplicates, and performs bulk insertion.
"""

import argparse
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy.exc import IntegrityError

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import SessionLocal
from models.company import Company
from scripts.utils import (
    DataLoadError,
    ProgressTracker,
    batch_insert,
    check_duplicate,
    get_db_session,
    log_data_quality_report,
    logger,
    safe_float,
    safe_int,
    validate_required_fields,
)

logger = logging.getLogger(__name__)


def load_companies_from_csv(csv_path: str) -> List[Dict]:
    """
    Load company data from CSV file.

    CSV should have columns:
    - ticker_symbol (required)
    - edinet_code
    - company_name_jp (required)
    - company_name_en
    - market_division
    - industry_code
    - industry_name
    - market_cap
    - shares_outstanding

    Args:
        csv_path: Path to CSV file

    Returns:
        List of company dictionaries

    Raises:
        DataLoadError: If CSV file cannot be read or is malformed
    """
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} companies from {csv_path}")

        # Convert DataFrame to list of dictionaries
        companies = []
        for _, row in df.iterrows():
            # Helper function to safely convert string fields, avoiding "nan" strings
            def safe_str_field(field_name: str) -> Optional[str]:
                """Convert field to string, return None if NaN or empty."""
                value = row.get(field_name)
                if pd.notna(value):
                    str_value = str(value).strip()
                    # Reject empty strings and literal "nan" string
                    if str_value and str_value.lower() != "nan":
                        return str_value
                return None

            company_data = {
                "ticker_symbol": safe_str_field("ticker_symbol"),
                "edinet_code": safe_str_field("edinet_code"),
                "company_name_jp": safe_str_field("company_name_jp"),
                "company_name_en": safe_str_field("company_name_en"),
                "market_division": safe_str_field("market_division"),
                "industry_code": safe_str_field("industry_code"),
                "industry_name": safe_str_field("industry_name"),
                "market_cap": safe_float(row.get("market_cap")),
                "shares_outstanding": safe_float(row.get("shares_outstanding")),
            }

            # Add optional fields if present
            if "fiscal_year_end" in df.columns and pd.notna(row.get("fiscal_year_end")):
                company_data["fiscal_year_end"] = str(
                    row.get("fiscal_year_end")
                ).strip()

            if "employee_count" in df.columns:
                company_data["employee_count"] = safe_int(row.get("employee_count"))

            if "website_url" in df.columns and pd.notna(row.get("website_url")):
                company_data["website_url"] = str(row.get("website_url")).strip()

            if "description" in df.columns and pd.notna(row.get("description")):
                company_data["description"] = str(row.get("description")).strip()

            companies.append(company_data)

        return companies

    except FileNotFoundError:
        raise DataLoadError(f"CSV file not found: {csv_path}")
    except pd.errors.EmptyDataError:
        raise DataLoadError(f"CSV file is empty: {csv_path}")
    except Exception as e:
        raise DataLoadError(f"Failed to load CSV: {str(e)}")


def validate_company_data(company: Dict) -> bool:
    """
    Validate company data has required fields.

    Args:
        company: Company dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["ticker_symbol", "company_name_jp"]
    return validate_required_fields(company, required_fields)


def insert_companies(
    companies: List[Dict], skip_duplicates: bool = True, batch_size: int = 100
) -> Dict[str, int]:
    """
    Insert companies into database.

    Args:
        companies: List of company dictionaries
        skip_duplicates: Whether to skip duplicate ticker symbols
        batch_size: Number of companies to insert per batch

    Returns:
        Dictionary with statistics (success, errors, duplicates, validation_failures)
    """
    stats = {
        "success": 0,
        "errors": 0,
        "duplicates": 0,
        "validation_failures": 0,
    }

    progress = ProgressTracker(len(companies), "Inserting companies")

    with get_db_session() as session:
        for company in companies:
            try:
                # Validate data
                if not validate_company_data(company):
                    stats["validation_failures"] += 1
                    progress.update(1, success=False)
                    continue

                # Check for duplicates
                if skip_duplicates and check_duplicate(
                    session, Company, "ticker_symbol", company["ticker_symbol"]
                ):
                    logger.debug(
                        f"Skipping duplicate company: {company['ticker_symbol']}"
                    )
                    stats["duplicates"] += 1
                    progress.update(1, success=True)
                    continue

                # Insert company
                db_company = Company(**company)
                session.add(db_company)
                session.commit()

                stats["success"] += 1
                progress.update(1, success=True)

            except IntegrityError as e:
                session.rollback()
                logger.warning(
                    f"Integrity error for company {company.get('ticker_symbol')}: {str(e)}"
                )
                stats["duplicates"] += 1
                progress.update(1, success=True)

            except Exception as e:
                session.rollback()
                logger.error(
                    f"Failed to insert company {company.get('ticker_symbol')}: {str(e)}"
                )
                stats["errors"] += 1
                progress.update(1, success=False)

    progress.close()
    return stats


def generate_sample_csv(output_path: str = "companies_sample.csv", num_samples: int = 10):
    """
    Generate a sample CSV file with example company data.

    This is useful for testing and as a template for actual data.

    Args:
        output_path: Path to output CSV file
        num_samples: Number of sample companies to generate
    """
    sample_data = []

    for i in range(num_samples):
        sample_data.append(
            {
                "ticker_symbol": f"{7200 + i}",
                "edinet_code": f"E0{10000 + i}",
                "company_name_jp": f"サンプル株式会社{i + 1}",
                "company_name_en": f"Sample Corporation {i + 1}",
                "market_division": "Prime",
                "industry_code": "5010",
                "industry_name": "Manufacturing",
                "market_cap": 1000000000.0 * (i + 1),
                "shares_outstanding": 100000000.0 * (i + 1),
                "fiscal_year_end": "03-31",
                "employee_count": 1000 * (i + 1),
                "website_url": f"https://example{i + 1}.co.jp",
                "description": f"Sample company {i + 1} for testing purposes",
            }
        )

    df = pd.DataFrame(sample_data)
    df.to_csv(output_path, index=False)
    logger.info(f"Generated sample CSV with {num_samples} companies at {output_path}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Initialize company master data in the database"
    )
    parser.add_argument(
        "--csv",
        type=str,
        help="Path to CSV file containing company data",
    )
    parser.add_argument(
        "--generate-sample",
        action="store_true",
        help="Generate a sample CSV file for testing",
    )
    parser.add_argument(
        "--sample-count",
        type=int,
        default=10,
        help="Number of sample companies to generate (default: 10)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for database insertions (default: 100)",
    )
    parser.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="Allow duplicate ticker symbols (default: skip duplicates)",
    )

    args = parser.parse_args()

    try:
        # Generate sample CSV if requested
        if args.generate_sample:
            generate_sample_csv(
                "companies_sample.csv", num_samples=args.sample_count
            )
            logger.info("Sample CSV generation complete")
            return 0

        # Load companies from CSV
        if not args.csv:
            logger.error("Please provide --csv argument or use --generate-sample")
            parser.print_help()
            return 1

        logger.info(f"Loading companies from: {args.csv}")
        companies = load_companies_from_csv(args.csv)

        if not companies:
            logger.warning("No companies to insert")
            return 1

        logger.info(f"Loaded {len(companies)} companies, starting insertion...")

        # Insert companies
        stats = insert_companies(
            companies,
            skip_duplicates=not args.allow_duplicates,
            batch_size=args.batch_size,
        )

        # Log summary
        log_data_quality_report(
            total=len(companies),
            success=stats["success"],
            errors=stats["errors"],
            duplicates=stats["duplicates"],
            validation_failures=stats["validation_failures"],
        )

        # Return exit code based on results
        if stats["errors"] > 0:
            logger.warning(f"Completed with {stats['errors']} errors")
            return 1

        logger.info("Company initialization completed successfully!")
        return 0

    except DataLoadError as e:
        logger.error(f"Data load error: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
