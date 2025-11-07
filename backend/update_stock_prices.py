#!/usr/bin/env python
"""Manual stock price update script for testing"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings
from models.company import Company
from models.financial import StockPrice
from services.yahoo_finance_client import YahooFinanceClient
from core.dependencies import get_redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_stock_prices():
    """Update stock prices for all companies"""
    # Create database session
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Initialize Yahoo Finance client
    redis_client = get_redis_client()
    yahoo_client = YahooFinanceClient(redis_client=redis_client)
    
    try:
        # Get all companies
        companies = db.query(Company).all()
        logger.info(f"Updating stock prices for {len(companies)} companies")
        
        success_count = 0
        for company in companies:
            try:
                # Get latest price from Yahoo Finance
                price_data = await yahoo_client.get_stock_price(
                    company.ticker_symbol, 
                    use_cache=False  # Force fresh data
                )
                
                if price_data:
                    # Check if data already exists for this date
                    existing = db.query(StockPrice).filter(
                        StockPrice.company_id == company.id,
                        StockPrice.date == datetime.strptime(price_data['date'], '%Y-%m-%d').date()
                    ).first()
                    
                    if existing:
                        # Update existing record
                        existing.open_price = price_data.get('open_price')
                        existing.high_price = price_data.get('high_price')
                        existing.low_price = price_data.get('low_price')
                        existing.close_price = price_data.get('close_price')
                        existing.volume = price_data.get('volume')
                        logger.info(f"Updated existing price for {company.ticker_symbol} on {price_data['date']}")
                    else:
                        # Create new record
                        new_price = StockPrice(
                            company_id=company.id,
                            date=datetime.strptime(price_data['date'], '%Y-%m-%d').date(),
                            open_price=price_data.get('open_price'),
                            high_price=price_data.get('high_price'),
                            low_price=price_data.get('low_price'),
                            close_price=price_data.get('close_price'),
                            volume=price_data.get('volume'),
                            data_source='yahoo_finance'
                        )
                        db.add(new_price)
                        logger.info(f"Added new price for {company.ticker_symbol} on {price_data['date']}")
                    
                    db.commit()
                    success_count += 1
                else:
                    logger.warning(f"No data received for {company.ticker_symbol}")
                    
            except Exception as e:
                logger.error(f"Error updating {company.ticker_symbol}: {e}")
                db.rollback()
                continue
        
        logger.info(f"Successfully updated {success_count}/{len(companies)} companies")
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(update_stock_prices())