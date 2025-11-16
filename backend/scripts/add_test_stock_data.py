#!/usr/bin/env python3
"""
Add test stock price data for chart testing.

This script adds realistic stock price data for testing the company details page
chart functionality. It generates 1 year of daily stock prices with realistic
price movements.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.company import Company
from models.financial import StockPrice
from core.config import settings

def generate_realistic_prices(
    company_id: int,
    start_price: float = 2000.0,
    days: int = 365
) -> list:
    """
    Generate realistic stock price data with random walk pattern.

    Args:
        company_id: Company ID
        start_price: Starting price
        days: Number of days of data to generate

    Returns:
        List of StockPrice objects
    """
    prices = []
    current_price = start_price
    end_date = datetime.now().date()

    for i in range(days):
        date = end_date - timedelta(days=days - i - 1)

        # Skip weekends
        if date.weekday() >= 5:
            continue

        # Random walk with slight upward bias
        change_percent = random.gauss(0.001, 0.02)  # Mean: +0.1%, Std: 2%
        daily_change = current_price * change_percent

        # Calculate OHLC prices
        open_price = current_price
        close_price = current_price + daily_change

        # High and low with some randomness
        high_price = max(open_price, close_price) * random.uniform(1.0, 1.02)
        low_price = min(open_price, close_price) * random.uniform(0.98, 1.0)

        # Volume with some randomness
        base_volume = 1_000_000
        volume = int(base_volume * random.uniform(0.5, 2.0))

        # Create StockPrice object
        stock_price = StockPrice(
            company_id=company_id,
            date=date,
            open_price=round(open_price, 2),
            high_price=round(high_price, 2),
            low_price=round(low_price, 2),
            close_price=round(close_price, 2),
            volume=volume,
            adjusted_close=round(close_price, 2),
            data_source="test_data"
        )

        prices.append(stock_price)
        current_price = close_price

    return prices

def add_test_stock_data():
    """Add test stock price data to database."""

    # Create database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("=" * 60)
        print("Adding Test Stock Price Data")
        print("=" * 60)

        # Get test companies (IDs 44-48)
        test_company_ids = [44, 45, 46, 47, 48]

        for company_id in test_company_ids:
            company = db.query(Company).filter(Company.id == company_id).first()

            if not company:
                print(f"⚠️  Company ID {company_id} not found, skipping...")
                continue

            # Check if stock prices already exist
            existing_count = db.query(StockPrice).filter(
                StockPrice.company_id == company_id
            ).count()

            if existing_count > 0:
                print(f"\n📊 Company ID {company_id} ({company.ticker_symbol}) already has {existing_count} stock prices")
                continue

            print(f"\n📈 Generating stock prices for Company ID {company_id}...")
            print(f"   Ticker: {company.ticker_symbol}")
            print(f"   Name: {company.company_name_jp}")

            # Generate stock prices
            # Use different starting prices for variety
            start_prices = {
                44: 2000.0,
                45: 3500.0,
                46: 1500.0,
                47: 2500.0,  # Main test company
                48: 4000.0
            }

            start_price = start_prices.get(company_id, 2000.0)
            stock_prices = generate_realistic_prices(
                company_id=company_id,
                start_price=start_price,
                days=365
            )

            # Add to database
            db.bulk_save_objects(stock_prices)
            db.commit()

            print(f"   ✅ Added {len(stock_prices)} stock prices")
            print(f"   📅 Date range: {stock_prices[0].date} to {stock_prices[-1].date}")
            print(f"   💰 Price range: ¥{min(p.close_price for p in stock_prices):.2f} - ¥{max(p.close_price for p in stock_prices):.2f}")

        print("\n" + "=" * 60)
        print("Stock Price Data Added Successfully!")
        print("=" * 60)
        print("\n🎯 Test these companies for chart functionality:")
        print("\n   Main test company (recommended):")
        print("   - http://localhost:3000/companies/47")
        print("\n   Other test companies:")
        for cid in [44, 45, 46, 48]:
            print(f"   - http://localhost:3000/companies/{cid}")
        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_test_stock_data()
