#!/usr/bin/env python3
"""
Check database for available data to test company details page.

This script checks which companies have complete data (stock prices,
financial statements, and indicators) for testing purposes.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models.company import Company
from models.financial import StockPrice, FinancialStatement, FinancialIndicator
from core.config import settings

def check_database_data():
    """Check what data is available in the database."""

    # Create database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("=" * 60)
        print("Database Data Check Report")
        print("=" * 60)

        # 1. Check companies
        total_companies = db.query(Company).count()
        print(f"\n1. Companies: {total_companies} total")

        if total_companies > 0:
            companies = db.query(Company).limit(10).all()
            print("\n   Sample companies:")
            for company in companies:
                print(f"   - ID: {company.id:4d} | {company.ticker_symbol:6s} | {company.company_name_jp}")

        # 2. Check stock prices
        stock_price_stats = db.query(
            StockPrice.company_id,
            Company.ticker_symbol,
            Company.company_name_jp,
            func.count(StockPrice.id).label('count'),
            func.min(StockPrice.date).label('min_date'),
            func.max(StockPrice.date).label('max_date')
        ).join(Company).group_by(
            StockPrice.company_id,
            Company.ticker_symbol,
            Company.company_name_jp
        ).all()

        print(f"\n2. Stock Prices: {len(stock_price_stats)} companies with data")
        if stock_price_stats:
            print("\n   Companies with stock price data:")
            for stat in stock_price_stats[:10]:
                print(f"   - ID: {stat.company_id:4d} | {stat.ticker_symbol:6s} | {stat.company_name_jp}")
                print(f"     └─ {stat.count} records ({stat.min_date} to {stat.max_date})")

        # 3. Check financial statements
        financial_stats = db.query(
            FinancialStatement.company_id,
            Company.ticker_symbol,
            Company.company_name_jp,
            func.count(FinancialStatement.id).label('count')
        ).join(Company).group_by(
            FinancialStatement.company_id,
            Company.ticker_symbol,
            Company.company_name_jp
        ).all()

        print(f"\n3. Financial Statements: {len(financial_stats)} companies with data")
        if financial_stats:
            print("\n   Companies with financial data:")
            for stat in financial_stats[:10]:
                print(f"   - ID: {stat.company_id:4d} | {stat.ticker_symbol:6s} | {stat.company_name_jp}")
                print(f"     └─ {stat.count} periods")

        # 4. Check financial indicators
        indicator_stats = db.query(
            FinancialIndicator.company_id,
            Company.ticker_symbol,
            Company.company_name_jp,
            func.count(FinancialIndicator.id).label('count')
        ).join(Company).group_by(
            FinancialIndicator.company_id,
            Company.ticker_symbol,
            Company.company_name_jp
        ).all()

        print(f"\n4. Financial Indicators: {len(indicator_stats)} companies with data")
        if indicator_stats:
            print("\n   Companies with indicator data:")
            for stat in indicator_stats[:10]:
                print(f"   - ID: {stat.company_id:4d} | {stat.ticker_symbol:6s} | {stat.company_name_jp}")
                print(f"     └─ {stat.count} periods")

        # 5. Find companies with ALL data types (best for testing)
        companies_with_prices = set([s.company_id for s in stock_price_stats])
        companies_with_financials = set([s.company_id for s in financial_stats])
        companies_with_indicators = set([s.company_id for s in indicator_stats])

        complete_companies = companies_with_prices & companies_with_financials & companies_with_indicators

        print("\n" + "=" * 60)
        print("RECOMMENDED FOR TESTING (Companies with ALL data types):")
        print("=" * 60)

        if complete_companies:
            for company_id in sorted(complete_companies)[:10]:
                company = db.query(Company).filter(Company.id == company_id).first()
                if company:
                    price_count = db.query(StockPrice).filter(StockPrice.company_id == company_id).count()
                    financial_count = db.query(FinancialStatement).filter(FinancialStatement.company_id == company_id).count()
                    indicator_count = db.query(FinancialIndicator).filter(FinancialIndicator.company_id == company_id).count()

                    print(f"\n✅ Company ID: {company.id}")
                    print(f"   Ticker: {company.ticker_symbol}")
                    print(f"   Name: {company.company_name_jp}")
                    print(f"   URL: http://localhost:3000/companies/{company.id}")
                    print(f"   Data: {price_count} prices, {financial_count} financials, {indicator_count} indicators")
        else:
            print("\n⚠️  No companies have complete data (stock + financial + indicators)")
            print("\n   Alternative test companies:")

            # Show companies with at least some data
            any_data_companies = companies_with_prices | companies_with_financials | companies_with_indicators
            if any_data_companies:
                for company_id in sorted(any_data_companies)[:5]:
                    company = db.query(Company).filter(Company.id == company_id).first()
                    if company:
                        has_prices = company_id in companies_with_prices
                        has_financials = company_id in companies_with_financials
                        has_indicators = company_id in companies_with_indicators

                        print(f"\n   Company ID: {company.id} | {company.ticker_symbol} | {company.company_name_jp}")
                        print(f"   └─ Prices: {'✓' if has_prices else '✗'} | "
                              f"Financials: {'✓' if has_financials else '✗'} | "
                              f"Indicators: {'✓' if has_indicators else '✗'}")
                        print(f"   └─ URL: http://localhost:3000/companies/{company.id}")

        print("\n" + "=" * 60)
        print("End of Report")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_database_data()