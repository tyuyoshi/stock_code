"""
Calculate and store financial indicators.

This script calculates financial indicators for all companies based on their
financial statements and stock price data. It uses the FinancialIndicatorEngine
to compute 60+ indicators including profitability, safety, efficiency, growth,
valuation, and cash flow metrics.
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import and_

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import SessionLocal
from models.company import Company
from models.financial import FinancialStatement, StockPrice, FinancialIndicator
from services.financial_indicators import FinancialIndicatorEngine, IndustryType
from scripts.utils import (
    DataLoadError,
    ProgressTracker,
    get_db_session,
    log_data_quality_report,
    logger,
    safe_float,
)

logger = logging.getLogger(__name__)


def get_stock_data(
    session: Session, company_id: int, target_date: datetime
) -> Optional[Dict[str, float]]:
    """
    Get stock price data for a company on or near a specific date.

    Args:
        session: SQLAlchemy session
        company_id: Company ID
        target_date: Target date for stock price

    Returns:
        Dictionary with stock price data or None if not available
    """
    # Try to get stock price for the exact date first
    stock_price = (
        session.query(StockPrice)
        .filter(
            and_(
                StockPrice.company_id == company_id,
                StockPrice.date == target_date,
            )
        )
        .first()
    )

    # If not found, try to get the closest date within 7 days
    if not stock_price:
        stock_price = (
            session.query(StockPrice)
            .filter(
                and_(
                    StockPrice.company_id == company_id,
                    StockPrice.date >= target_date - timedelta(days=7),
                    StockPrice.date <= target_date + timedelta(days=7),
                )
            )
            .order_by(StockPrice.date.desc())
            .first()
        )

    if not stock_price:
        return None

    return {
        "current_price": safe_float(stock_price.close_price),
        "market_cap": 0.0,  # Will be calculated if shares_outstanding is available
        "volume": safe_float(stock_price.volume),
    }


def get_previous_financial_data(
    session: Session, company_id: int, current_year: int, current_quarter: Optional[int]
) -> Optional[Dict[str, float]]:
    """
    Get previous period financial data for growth calculations.

    Args:
        session: SQLAlchemy session
        company_id: Company ID
        current_year: Current fiscal year
        current_quarter: Current fiscal quarter (or None for annual)

    Returns:
        Dictionary with previous period financial data or None
    """
    if current_quarter:
        # Get same quarter from previous year
        prev_year = current_year - 1
        prev_quarter = current_quarter
    else:
        # Get previous annual data
        prev_year = current_year - 1
        prev_quarter = None

    prev_financial = (
        session.query(FinancialStatement)
        .filter(
            and_(
                FinancialStatement.company_id == company_id,
                FinancialStatement.fiscal_year == prev_year,
                FinancialStatement.fiscal_quarter == prev_quarter,
            )
        )
        .first()
    )

    if not prev_financial:
        return None

    return {
        "revenue": safe_float(prev_financial.revenue),
        "net_income": safe_float(prev_financial.net_income),
        "total_assets": safe_float(prev_financial.total_assets),
        "shareholders_equity": safe_float(prev_financial.shareholders_equity),
    }


def financial_statement_to_dict(financial: FinancialStatement) -> Dict[str, float]:
    """
    Convert FinancialStatement model to dictionary for indicator calculation.

    Args:
        financial: FinancialStatement model instance

    Returns:
        Dictionary with financial data
    """
    return {
        # Income Statement
        "revenue": safe_float(financial.revenue),
        "cost_of_revenue": safe_float(financial.cost_of_revenue),
        "gross_profit": safe_float(financial.gross_profit),
        "operating_expenses": safe_float(financial.operating_expenses),
        "operating_income": safe_float(financial.operating_income),
        "net_income": safe_float(financial.net_income),
        # Balance Sheet
        "total_assets": safe_float(financial.total_assets),
        "current_assets": safe_float(financial.current_assets),
        "total_liabilities": safe_float(financial.total_liabilities),
        "current_liabilities": safe_float(financial.current_liabilities),
        "shareholders_equity": safe_float(financial.shareholders_equity),
        # Cash Flow
        "operating_cash_flow": safe_float(financial.operating_cash_flow),
        "investing_cash_flow": safe_float(financial.investing_cash_flow),
        "financing_cash_flow": safe_float(financial.financing_cash_flow),
        "free_cash_flow": safe_float(financial.free_cash_flow),
    }


def calculate_indicators_for_company(
    session: Session,
    company: Company,
    engine: FinancialIndicatorEngine,
) -> int:
    """
    Calculate indicators for all financial statements of a company.

    Args:
        session: SQLAlchemy session
        company: Company model instance
        engine: FinancialIndicatorEngine instance

    Returns:
        Number of indicators calculated
    """
    # Get all financial statements for this company
    financials = (
        session.query(FinancialStatement)
        .filter(FinancialStatement.company_id == company.id)
        .order_by(
            FinancialStatement.fiscal_year.desc(),
            FinancialStatement.fiscal_quarter.desc(),
        )
        .all()
    )

    if not financials:
        logger.warning(f"No financial data found for {company.ticker_symbol}")
        return 0

    count = 0

    for financial in financials:
        try:
            # Check if indicators already exist for this financial statement
            existing = (
                session.query(FinancialIndicator)
                .filter(
                    and_(
                        FinancialIndicator.company_id == company.id,
                        FinancialIndicator.date == financial.period_end,
                    )
                )
                .first()
            )

            if existing:
                logger.debug(
                    f"Skipping existing indicators for {company.ticker_symbol} "
                    f"FY{financial.fiscal_year} Q{financial.fiscal_quarter}"
                )
                continue

            # Convert financial statement to dictionary
            financial_data = financial_statement_to_dict(financial)

            # Get stock data for valuation indicators
            stock_data = get_stock_data(session, company.id, financial.period_end)

            # Get previous period data for growth indicators
            previous_data = get_previous_financial_data(
                session,
                company.id,
                financial.fiscal_year,
                financial.fiscal_quarter,
            )

            # Determine industry type (simplified - can be enhanced)
            industry_type = None  # Can be mapped from company.industry_code

            # Calculate all indicators
            indicators = engine.calculate_all_indicators(
                financial_data=financial_data,
                stock_data=stock_data,
                previous_data=previous_data,
                industry_type=industry_type,
            )

            # Flatten the indicator dictionary and create FinancialIndicator record
            indicator_record = FinancialIndicator(
                company_id=company.id,
                date=financial.period_end,
                # Profitability
                roe=indicators["profitability"].get("roe"),
                roa=indicators["profitability"].get("roa"),
                gross_margin=indicators["profitability"].get("gross_margin"),
                operating_margin=indicators["profitability"].get("operating_margin"),
                net_margin=indicators["profitability"].get("net_margin"),
                # Valuation
                per=indicators["valuation"].get("per") if "valuation" in indicators else None,
                pbr=indicators["valuation"].get("pbr") if "valuation" in indicators else None,
                psr=indicators["valuation"].get("psr") if "valuation" in indicators else None,
                ev_ebitda=indicators["valuation"].get("ev_ebitda") if "valuation" in indicators else None,
                # Growth
                revenue_growth_yoy=indicators["growth"].get("revenue_growth")
                if "growth" in indicators
                else None,
                earnings_growth_yoy=indicators["growth"].get("earnings_growth")
                if "growth" in indicators
                else None,
                # Financial Health
                current_ratio=indicators["safety"].get("current_ratio"),
                debt_to_equity=indicators["safety"].get("debt_to_equity"),
                interest_coverage=indicators["safety"].get("interest_coverage"),
                # Dividend
                dividend_yield=indicators["valuation"].get("dividend_yield")
                if "valuation" in indicators
                else None,
                payout_ratio=indicators["valuation"].get("payout_ratio")
                if "valuation" in indicators
                else None,
            )

            session.add(indicator_record)
            session.commit()
            count += 1

        except Exception as e:
            session.rollback()
            logger.error(
                f"Failed to calculate indicators for {company.ticker_symbol} "
                f"FY{financial.fiscal_year} Q{financial.fiscal_quarter}: {str(e)}"
            )

    return count


def calculate_all_indicators(batch_size: int = 50) -> Dict[str, int]:
    """
    Calculate indicators for all companies.

    Args:
        batch_size: Number of companies to process before committing

    Returns:
        Dictionary with statistics
    """
    stats = {
        "companies_processed": 0,
        "companies_failed": 0,
        "indicators_calculated": 0,
    }

    with get_db_session() as session:
        # Get all companies
        companies = session.query(Company).all()
        logger.info(f"Calculating indicators for {len(companies)} companies")

        # Initialize indicator engine
        engine = FinancialIndicatorEngine()

        progress = ProgressTracker(len(companies), "Calculating indicators")

        for company in companies:
            try:
                count = calculate_indicators_for_company(session, company, engine)
                stats["indicators_calculated"] += count
                stats["companies_processed"] += 1
                progress.update(1, success=True)

            except Exception as e:
                logger.error(
                    f"Failed to process company {company.ticker_symbol}: {str(e)}"
                )
                stats["companies_failed"] += 1
                progress.update(1, success=False)

        progress.close()

    return stats


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Calculate and store financial indicators"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Batch size for processing (default: 50)",
    )

    args = parser.parse_args()

    try:
        logger.info("Starting financial indicator calculation...")

        # Calculate all indicators
        stats = calculate_all_indicators(batch_size=args.batch_size)

        # Log summary
        logger.info("=" * 60)
        logger.info("CALCULATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Companies processed: {stats['companies_processed']}")
        logger.info(f"Companies failed: {stats['companies_failed']}")
        logger.info(f"Indicators calculated: {stats['indicators_calculated']}")
        logger.info("=" * 60)

        if stats["companies_failed"] > 0:
            logger.warning(f"Completed with {stats['companies_failed']} failures")
            return 1

        logger.info("Financial indicator calculation completed successfully!")
        return 0

    except DataLoadError as e:
        logger.error(f"Data load error: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
