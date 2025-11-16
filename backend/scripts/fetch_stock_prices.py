"""
Fetch and load stock price data.

This script fetches historical stock price data for companies from Yahoo Finance API
and loads it into the database. It includes rate limiting and error handling.
"""

import argparse
import logging
import sys
import time
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import SessionLocal
from models.company import Company
from models.financial import StockPrice
from services.yahoo_finance_client import YahooFinanceClient
from scripts.utils import (
    DataLoadError,
    ProgressTracker,
    get_db_session,
    log_data_quality_report,
    logger,
    retry_on_error,
    safe_float,
)

logger = logging.getLogger(__name__)


def load_stock_prices_from_csv(csv_path: str) -> List[Dict]:
    """
    Load stock price data from CSV file.

    CSV should have columns:
    - ticker_symbol (required)
    - date (required, YYYY-MM-DD format)
    - open_price
    - high_price
    - low_price
    - close_price
    - adjusted_close
    - volume
    - data_source (optional, default: 'csv')

    Args:
        csv_path: Path to CSV file

    Returns:
        List of stock price dictionaries

    Raises:
        DataLoadError: If CSV file cannot be read
    """
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} stock price records from {csv_path}")

        stock_prices = []
        for _, row in df.iterrows():
            price_data = {
                "ticker_symbol": str(row.get("ticker_symbol", "")).strip(),
                "date": pd.to_datetime(row.get("date")).date()
                if pd.notna(row.get("date"))
                else None,
                "open_price": safe_float(row.get("open_price")),
                "high_price": safe_float(row.get("high_price")),
                "low_price": safe_float(row.get("low_price")),
                "close_price": safe_float(row.get("close_price")),
                "adjusted_close": safe_float(row.get("adjusted_close")),
                "volume": safe_float(row.get("volume")),
                "data_source": str(row.get("data_source", "csv")).strip(),
            }

            stock_prices.append(price_data)

        return stock_prices

    except FileNotFoundError:
        raise DataLoadError(f"CSV file not found: {csv_path}")
    except Exception as e:
        raise DataLoadError(f"Failed to load CSV: {str(e)}")


def fetch_from_yahoo_finance(
    session: Session,
    ticker_symbol: str,
    start_date: date,
    end_date: date,
    yahoo_client: YahooFinanceClient,
) -> List[Dict]:
    """
    Fetch stock price data from Yahoo Finance for a single company.

    Args:
        session: SQLAlchemy session
        ticker_symbol: Company ticker symbol
        start_date: Start date for historical data
        end_date: End date for historical data
        yahoo_client: Yahoo Finance client instance

    Returns:
        List of stock price dictionaries
    """
    try:
        # Fetch historical data
        hist_data = yahoo_client.get_historical_data(
            ticker=ticker_symbol,
            start_date=start_date,
            end_date=end_date,
        )

        if not hist_data or hist_data.empty:
            logger.warning(f"No data returned for {ticker_symbol}")
            return []

        # Convert DataFrame to list of dictionaries
        stock_prices = []
        for date_idx, row in hist_data.iterrows():
            price_data = {
                "ticker_symbol": ticker_symbol,
                "date": date_idx.date() if hasattr(date_idx, 'date') else date_idx,
                "open_price": safe_float(row.get("Open")),
                "high_price": safe_float(row.get("High")),
                "low_price": safe_float(row.get("Low")),
                "close_price": safe_float(row.get("Close")),
                "adjusted_close": safe_float(row.get("Adj Close")),
                "volume": safe_float(row.get("Volume")),
                "data_source": "yahoo_finance",
            }
            stock_prices.append(price_data)

        logger.info(f"Fetched {len(stock_prices)} price records for {ticker_symbol}")
        return stock_prices

    except Exception as e:
        logger.error(f"Failed to fetch data for {ticker_symbol}: {str(e)}")
        return []


def insert_stock_prices(
    session: Session, stock_prices: List[Dict]
) -> Dict[str, int]:
    """
    Insert stock prices into database.

    Args:
        session: SQLAlchemy session
        stock_prices: List of stock price dictionaries

    Returns:
        Dictionary with statistics (success, errors, duplicates, validation_failures)
    """
    stats = {
        "success": 0,
        "errors": 0,
        "duplicates": 0,
        "validation_failures": 0,
    }

    progress = ProgressTracker(len(stock_prices), "Inserting stock prices")

    for price_data in stock_prices:
        try:
            # Validate required fields
            if not price_data.get("ticker_symbol") or not price_data.get("date"):
                stats["validation_failures"] += 1
                progress.update(1, success=False)
                continue

            # Get company by ticker symbol
            ticker = price_data.pop("ticker_symbol")
            company = session.query(Company).filter(
                Company.ticker_symbol == ticker
            ).first()

            if not company:
                logger.warning(f"Company not found: {ticker}")
                stats["errors"] += 1
                progress.update(1, success=False)
                continue

            # Add company_id to price data
            price_data["company_id"] = company.id

            # Check for duplicate (same company, same date)
            existing = session.query(StockPrice).filter(
                StockPrice.company_id == company.id,
                StockPrice.date == price_data["date"],
            ).first()

            if existing:
                stats["duplicates"] += 1
                progress.update(1, success=True)
                continue

            # Insert stock price
            db_price = StockPrice(**price_data)
            session.add(db_price)
            session.commit()

            stats["success"] += 1
            progress.update(1, success=True)

        except IntegrityError as e:
            session.rollback()
            stats["duplicates"] += 1
            progress.update(1, success=True)

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to insert stock price: {str(e)}")
            stats["errors"] += 1
            progress.update(1, success=False)

    progress.close()
    return stats


def fetch_all_companies(
    session: Session,
    start_date: date,
    end_date: date,
    batch_size: int = 50,
    rate_limit_delay: float = 0.5,
) -> Dict[str, int]:
    """
    Fetch stock price data for all companies from Yahoo Finance.

    Args:
        session: SQLAlchemy session
        start_date: Start date for historical data
        end_date: End date for historical data
        batch_size: Number of companies to process before committing
        rate_limit_delay: Delay between API calls in seconds

    Returns:
        Dictionary with statistics
    """
    # Get all companies from database
    companies = session.query(Company).all()
    logger.info(f"Fetching stock prices for {len(companies)} companies")

    # Initialize Yahoo Finance client
    yahoo_client = YahooFinanceClient()

    total_stats = {
        "success": 0,
        "errors": 0,
        "duplicates": 0,
        "validation_failures": 0,
        "companies_processed": 0,
        "companies_failed": 0,
    }

    progress = ProgressTracker(len(companies), "Processing companies")

    for company in companies:
        try:
            # Fetch data for this company
            stock_prices = fetch_from_yahoo_finance(
                session,
                company.ticker_symbol,
                start_date,
                end_date,
                yahoo_client,
            )

            if stock_prices:
                # Insert stock prices
                stats = insert_stock_prices(session, stock_prices)
                total_stats["success"] += stats["success"]
                total_stats["errors"] += stats["errors"]
                total_stats["duplicates"] += stats["duplicates"]
                total_stats["validation_failures"] += stats["validation_failures"]
                total_stats["companies_processed"] += 1
            else:
                total_stats["companies_failed"] += 1

            progress.update(1, success=True)

            # Rate limiting
            time.sleep(rate_limit_delay)

        except Exception as e:
            logger.error(f"Failed to process company {company.ticker_symbol}: {str(e)}")
            total_stats["companies_failed"] += 1
            progress.update(1, success=False)

    progress.close()
    return total_stats


def generate_sample_csv(
    output_path: str = "stock_prices_sample.csv", num_days: int = 30
):
    """
    Generate a sample CSV file with example stock price data.

    Args:
        output_path: Path to output CSV file
        num_days: Number of days of data to generate
    """
    sample_data = []

    # Generate data for 5 companies over num_days
    base_date = datetime.now().date()
    for company_idx in range(5):
        ticker = f"{7200 + company_idx}"
        base_price = 1000.0 + (company_idx * 100)

        for day in range(num_days):
            current_date = base_date - timedelta(days=day)
            variation = (day % 10 - 5) * 10  # Simple price variation

            sample_data.append(
                {
                    "ticker_symbol": ticker,
                    "date": current_date.strftime("%Y-%m-%d"),
                    "open_price": base_price + variation,
                    "high_price": base_price + variation + 20,
                    "low_price": base_price + variation - 20,
                    "close_price": base_price + variation + 5,
                    "adjusted_close": base_price + variation + 5,
                    "volume": 1000000.0 + (day * 10000),
                    "data_source": "sample",
                }
            )

    df = pd.DataFrame(sample_data)
    df.to_csv(output_path, index=False)
    logger.info(f"Generated sample CSV with {len(sample_data)} stock price records at {output_path}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Fetch and load stock price data"
    )
    parser.add_argument(
        "--csv",
        type=str,
        help="Path to CSV file containing stock price data",
    )
    parser.add_argument(
        "--generate-sample",
        action="store_true",
        help="Generate a sample CSV file for testing",
    )
    parser.add_argument(
        "--yahoo",
        action="store_true",
        help="Fetch data from Yahoo Finance for all companies",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for historical data (YYYY-MM-DD, default: 1 year ago)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date for historical data (YYYY-MM-DD, default: today)",
    )
    parser.add_argument(
        "--rate-limit-delay",
        type=float,
        default=0.5,
        help="Delay between API calls in seconds (default: 0.5)",
    )

    args = parser.parse_args()

    try:
        # Generate sample CSV if requested
        if args.generate_sample:
            generate_sample_csv("stock_prices_sample.csv", num_days=30)
            logger.info("Sample CSV generation complete")
            return 0

        # Parse dates
        if args.start_date:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        else:
            start_date = (datetime.now() - timedelta(days=365)).date()

        if args.end_date:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
        else:
            end_date = datetime.now().date()

        logger.info(f"Date range: {start_date} to {end_date}")

        # Load from CSV or Yahoo Finance
        if args.csv:
            logger.info(f"Loading stock price data from: {args.csv}")
            stock_prices = load_stock_prices_from_csv(args.csv)

            with get_db_session() as session:
                stats = insert_stock_prices(session, stock_prices)

            log_data_quality_report(
                total=len(stock_prices),
                success=stats["success"],
                errors=stats["errors"],
                duplicates=stats["duplicates"],
                validation_failures=stats["validation_failures"],
            )

        elif args.yahoo:
            logger.info("Fetching stock price data from Yahoo Finance...")

            with get_db_session() as session:
                stats = fetch_all_companies(
                    session,
                    start_date,
                    end_date,
                    rate_limit_delay=args.rate_limit_delay,
                )

            logger.info(f"Companies processed: {stats['companies_processed']}")
            logger.info(f"Companies failed: {stats['companies_failed']}")
            log_data_quality_report(
                total=stats["success"] + stats["errors"],
                success=stats["success"],
                errors=stats["errors"],
                duplicates=stats["duplicates"],
                validation_failures=stats["validation_failures"],
            )

        else:
            logger.error("Please provide --csv or --yahoo argument, or use --generate-sample")
            parser.print_help()
            return 1

        logger.info("Stock price data loading completed successfully!")
        return 0

    except DataLoadError as e:
        logger.error(f"Data load error: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
