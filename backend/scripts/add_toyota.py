"""Add Toyota Motor Corporation to database for testing intraday data"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.company import Company
from core.database import SessionLocal


def main():
    """Add or update Toyota Motor Corporation"""
    db = SessionLocal()

    try:
        # Check if already exists
        existing = db.query(Company).filter(Company.ticker_symbol == "7203").first()

        if existing:
            # Update existing company with real Toyota data
            print(f"Updating existing company ID={existing.id} to Toyota data...")
            existing.company_name_jp = "トヨタ自動車株式会社"
            existing.company_name_en = "Toyota Motor Corporation"
            existing.market_division = "東証プライム"
            existing.industry_name = "輸送用機器"
            existing.description = "日本を代表する自動車メーカー"

            db.commit()
            db.refresh(existing)
            toyota = existing
            print("✅ Updated existing company")
        else:
            # Add new Toyota
            toyota = Company(
                ticker_symbol="7203",
                company_name_jp="トヨタ自動車株式会社",
                company_name_en="Toyota Motor Corporation",
                market_division="東証プライム",
                industry_name="輸送用機器",
                description="日本を代表する自動車メーカー"
            )

            db.add(toyota)
            db.commit()
            db.refresh(toyota)
            print("✅ Added new company")

        print(f"✅ Successfully added Toyota:")
        print(f"   ID: {toyota.id}")
        print(f"   Ticker: {toyota.ticker_symbol}")
        print(f"   Name: {toyota.company_name_jp}")
        print(f"\nYou can now test intraday data with:")
        print(f"   curl 'http://localhost:8000/api/v1/stock-prices/7203/chart?period=1d&interval=15m'")
        print(f"\nOr access via frontend:")
        print(f"   http://localhost:3000/companies/{toyota.id}")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
