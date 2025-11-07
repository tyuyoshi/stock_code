"""Daily Update Batch Job"""

import logging
from datetime import datetime, timedelta
from typing import List
import asyncio

try:
    from ..services.edinet_client import EDINETClient
    from ..services.data_processor import DataProcessor
    from ..services.yahoo_finance_client import YahooFinanceClient
    from ..services.trading_calendar import is_trading_day
    from ..services.notification import (
        NotificationService, 
        BatchJobResult, 
        NotificationLevel,
        notify_batch_result
    )
    from ..core.database import SessionLocal
    from ..models.company import Company
    from ..models.financial import StockPrice, FinancialIndicator
    from ..core.config import settings
except ImportError:
    from services.edinet_client import EDINETClient
    from services.data_processor import DataProcessor
    from services.yahoo_finance_client import YahooFinanceClient
    from services.trading_calendar import is_trading_day
    from services.notification import (
        NotificationService, 
        BatchJobResult, 
        NotificationLevel,
        notify_batch_result
    )
    from core.database import SessionLocal
    from models.company import Company
    from models.financial import StockPrice, FinancialIndicator
    from core.config import settings

from sqlalchemy.exc import IntegrityError
from redis import Redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DailyUpdateJob:
    """Daily batch job for updating stock and financial data"""

    def __init__(self):
        self.edinet_client = EDINETClient()
        self.data_processor = DataProcessor()
        self.db = SessionLocal()
        self.notification_service = NotificationService()
        
        # Initialize Redis client for caching (optional)
        self.redis_client = None
        try:
            if settings.redis_url:
                self.redis_client = Redis.from_url(settings.redis_url)
                logger.info("Redis client initialized for caching")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis client: {e}")
        
        self.yahoo_client = YahooFinanceClient(redis_client=self.redis_client)
    
    async def run(self):
        """Main entry point for daily update job"""
        start_time = datetime.now()
        error_messages = []
        total_companies = 0
        successful_companies = 0
        
        try:
            logger.info("Starting daily update job")
            
            # Check if today is a trading day
            if not is_trading_day():
                logger.info("Today is not a trading day, skipping update")
                return
            
            # Get list of companies to update
            companies = self.get_active_companies()
            total_companies = len(companies)
            logger.info(f"Found {total_companies} companies to update")
            
            # Update stock prices
            successful_companies = await self.update_stock_prices(companies)
            
            # Update financial indicators (if needed)
            # await self.update_financial_indicators(companies)
            
            # Clean up old data
            self.cleanup_old_data()
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Create result object
            status = "success" if successful_companies == total_companies else "partial_success"
            result = BatchJobResult(
                job_name="Daily Stock Price Update",
                start_time=start_time,
                end_time=end_time,
                status=status,
                total_items=total_companies,
                successful_items=successful_companies,
                failed_items=total_companies - successful_companies,
                error_messages=error_messages,
                execution_time_seconds=execution_time
            )
            
            # Send notification
            self.notification_service.notify_batch_result(result)
            
            logger.info(f"Daily update job completed. Success: {successful_companies}/{total_companies}")
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            error_msg = f"Daily update job failed: {e}"
            logger.error(error_msg)
            error_messages.append(error_msg)
            
            # Create failure result
            result = BatchJobResult(
                job_name="Daily Stock Price Update",
                start_time=start_time,
                end_time=end_time,
                status="failure",
                total_items=total_companies,
                successful_items=successful_companies,
                failed_items=total_companies - successful_companies,
                error_messages=error_messages,
                execution_time_seconds=execution_time
            )
            
            # Send error notification
            self.notification_service.notify_batch_result(result, NotificationLevel.ERROR)
            
            raise
        finally:
            self.db.close()
    
    def get_active_companies(self) -> List[Company]:
        """Get list of active companies"""
        return self.db.query(Company).all()
    
    async def update_stock_prices(self, companies: List[Company]) -> int:
        """Update stock prices for all companies"""
        logger.info(f"Starting stock price update for {len(companies)} companies")
        
        success_count = 0
        error_count = 0
        
        # Process companies in batches to avoid overwhelming the API
        batch_size = 10
        for i in range(0, len(companies), batch_size):
            batch = companies[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(companies) + batch_size - 1)//batch_size}")
            
            # Fetch stock prices for the batch
            ticker_symbols = [company.ticker_symbol for company in batch]
            price_data_batch = await self.yahoo_client.bulk_fetch_prices(ticker_symbols)
            
            # Process each company's data
            for company in batch:
                try:
                    price_data = price_data_batch.get(company.ticker_symbol)
                    
                    if not price_data:
                        logger.warning(f"No price data received for {company.ticker_symbol}")
                        error_count += 1
                        continue
                    
                    # Check if we already have data for today
                    today = datetime.now().date()
                    existing_record = self.db.query(StockPrice).filter(
                        StockPrice.company_id == company.id,
                        StockPrice.date == today
                    ).first()
                    
                    if existing_record:
                        # Update existing record
                        existing_record.open_price = price_data.get('open_price')
                        existing_record.high_price = price_data.get('high_price')
                        existing_record.low_price = price_data.get('low_price')
                        existing_record.close_price = price_data.get('close_price')
                        existing_record.volume = price_data.get('volume')
                        existing_record.data_source = "yahoo_finance"
                        logger.debug(f"Updated existing record for {company.ticker_symbol}")
                    else:
                        # Create new record for today
                        stock_price = StockPrice(
                            company_id=company.id,
                            date=today,
                            open_price=price_data.get('open_price'),
                            high_price=price_data.get('high_price'),
                            low_price=price_data.get('low_price'),
                            close_price=price_data.get('close_price'),
                            volume=price_data.get('volume'),
                            data_source="yahoo_finance"
                        )
                        self.db.add(stock_price)
                        logger.debug(f"Created new record for {company.ticker_symbol}")
                    
                    success_count += 1
                    
                except IntegrityError as e:
                    logger.debug(f"Duplicate record for {company.ticker_symbol}: {e}")
                    self.db.rollback()
                    error_count += 1
                except Exception as e:
                    logger.error(f"Failed to update stock price for {company.ticker_symbol}: {e}")
                    self.db.rollback()
                    error_count += 1
            
            # Commit changes for this batch
            try:
                self.db.commit()
                logger.debug(f"Committed batch {i//batch_size + 1}")
            except Exception as e:
                logger.error(f"Failed to commit batch {i//batch_size + 1}: {e}")
                self.db.rollback()
            
            # Small delay between batches
            if i + batch_size < len(companies):
                await asyncio.sleep(2)
        
        logger.info(f"Stock price update completed. Success: {success_count}, Errors: {error_count}")
        return success_count
    
    async def update_financial_indicators(self, companies: List[Company]):
        """Calculate and update financial indicators"""
        for company in companies:
            try:
                # Get latest financial data
                # Calculate indicators
                # Save to database
                pass
            except Exception as e:
                logger.error(f"Failed to update indicators for {company.ticker_symbol}: {e}")
    
    def cleanup_old_data(self, days_to_keep: int = 365):
        """Clean up data older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        # TODO: Implement cleanup logic
        pass


def main():
    """Entry point for the script"""
    job = DailyUpdateJob()
    asyncio.run(job.run())


if __name__ == "__main__":
    main()