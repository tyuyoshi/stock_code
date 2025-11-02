"""Backfill Script for Stock Price Historical Data"""

import asyncio
import logging
import sys
import argparse
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

# Add backend to path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from core.database import SessionLocal
from models.company import Company
from models.financial import StockPrice
from services.yahoo_finance_client import YahooFinanceClient
from sqlalchemy.exc import IntegrityError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StockPriceBackfiller:
    """Backfill historical stock price data from Yahoo Finance"""
    
    def __init__(self, batch_size: int = 50, delay_between_batches: int = 10):
        """Initialize backfiller
        
        Args:
            batch_size: Number of companies to process in each batch
            delay_between_batches: Delay in seconds between batches
        """
        self.db = SessionLocal()
        self.yahoo_client = YahooFinanceClient()
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.success_count = 0
        self.error_count = 0
        self.total_records_inserted = 0
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    async def get_companies_to_backfill(self, ticker_symbols: Optional[List[str]] = None) -> List[Company]:
        """Get list of companies that need backfilling
        
        Args:
            ticker_symbols: Optional list of specific tickers to backfill
            
        Returns:
            List of Company objects
        """
        query = self.db.query(Company)
        
        if ticker_symbols:
            query = query.filter(Company.ticker_symbol.in_(ticker_symbols))
        
        companies = query.all()
        logger.info(f"Found {len(companies)} companies to backfill")
        return companies
    
    async def backfill_company(
        self, 
        company: Company, 
        period: str = "5y",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> bool:
        """Backfill historical data for a single company
        
        Args:
            company: Company object
            period: Period to backfill (5y, 2y, 1y, etc.)
            start_date: Optional start date in YYYY-MM-DD format
            end_date: Optional end date in YYYY-MM-DD format
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Backfilling data for {company.ticker_symbol} ({company.company_name_jp})")
            
            # Check if we already have recent data
            existing_data = self.db.query(StockPrice).filter(
                StockPrice.company_id == company.id
            ).order_by(StockPrice.date.desc()).first()
            
            if existing_data:
                days_since_last = (datetime.now().date() - existing_data.date).days
                if days_since_last < 7:  # If we have data from within a week
                    logger.info(f"Skipping {company.ticker_symbol} - recent data exists (last: {existing_data.date})")
                    return True
            
            # Fetch historical data from Yahoo Finance
            historical_data = await self.yahoo_client.get_historical_data(
                company.ticker_symbol,
                period=period,
                start_date=start_date,
                end_date=end_date
            )
            
            if not historical_data:
                logger.warning(f"No historical data found for {company.ticker_symbol}")
                return False
            
            # Insert data into database
            records_inserted = 0
            for price_data in historical_data:
                try:
                    # Check if record already exists
                    existing_record = self.db.query(StockPrice).filter(
                        StockPrice.company_id == company.id,
                        StockPrice.date == datetime.strptime(price_data['date'], '%Y-%m-%d').date()
                    ).first()
                    
                    if existing_record:
                        # Update existing record
                        existing_record.open_price = price_data.get('open_price')
                        existing_record.high_price = price_data.get('high_price')
                        existing_record.low_price = price_data.get('low_price')
                        existing_record.close_price = price_data.get('close_price')
                        existing_record.volume = price_data.get('volume')
                        existing_record.data_source = "yahoo_finance"
                        logger.debug(f"Updated existing record for {company.ticker_symbol} on {price_data['date']}")
                    else:
                        # Create new record
                        stock_price = StockPrice(
                            company_id=company.id,
                            date=datetime.strptime(price_data['date'], '%Y-%m-%d').date(),
                            open_price=price_data.get('open_price'),
                            high_price=price_data.get('high_price'),
                            low_price=price_data.get('low_price'),
                            close_price=price_data.get('close_price'),
                            volume=price_data.get('volume'),
                            data_source="yahoo_finance"
                        )
                        self.db.add(stock_price)
                        records_inserted += 1
                
                except IntegrityError as e:
                    logger.debug(f"Duplicate record for {company.ticker_symbol} on {price_data['date']}: {e}")
                    self.db.rollback()
                    continue
                except Exception as e:
                    logger.error(f"Error inserting record for {company.ticker_symbol} on {price_data['date']}: {e}")
                    self.db.rollback()
                    continue
            
            # Commit all changes for this company
            self.db.commit()
            self.total_records_inserted += records_inserted
            
            logger.info(f"Successfully backfilled {records_inserted} records for {company.ticker_symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backfill data for {company.ticker_symbol}: {e}")
            self.db.rollback()
            return False
    
    async def run_backfill(
        self,
        ticker_symbols: Optional[List[str]] = None,
        period: str = "5y",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> None:
        """Run the backfill process
        
        Args:
            ticker_symbols: Optional list of specific tickers to backfill
            period: Period to backfill (5y, 2y, 1y, etc.)
            start_date: Optional start date in YYYY-MM-DD format
            end_date: Optional end date in YYYY-MM-DD format
        """
        start_time = datetime.now()
        logger.info(f"Starting stock price backfill at {start_time}")
        
        # Get companies to process
        companies = await self.get_companies_to_backfill(ticker_symbols)
        
        if not companies:
            logger.warning("No companies found to backfill")
            return
        
        # Process companies in batches
        for i in range(0, len(companies), self.batch_size):
            batch = companies[i:i + self.batch_size]
            batch_start = datetime.now()
            
            logger.info(f"Processing batch {i//self.batch_size + 1}/{(len(companies) + self.batch_size - 1)//self.batch_size} "
                       f"({len(batch)} companies)")
            
            # Process batch
            for company in batch:
                success = await self.backfill_company(
                    company, 
                    period=period,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if success:
                    self.success_count += 1
                else:
                    self.error_count += 1
                
                # Small delay between individual requests
                await asyncio.sleep(0.5)
            
            batch_duration = datetime.now() - batch_start
            logger.info(f"Batch completed in {batch_duration.total_seconds():.1f} seconds")
            
            # Delay between batches (except for the last batch)
            if i + self.batch_size < len(companies):
                logger.info(f"Waiting {self.delay_between_batches} seconds before next batch...")
                await asyncio.sleep(self.delay_between_batches)
        
        # Final statistics
        end_time = datetime.now()
        total_duration = end_time - start_time
        
        logger.info("="*60)
        logger.info("BACKFILL SUMMARY")
        logger.info("="*60)
        logger.info(f"Start time: {start_time}")
        logger.info(f"End time: {end_time}")
        logger.info(f"Total duration: {total_duration}")
        logger.info(f"Companies processed: {len(companies)}")
        logger.info(f"Successful: {self.success_count}")
        logger.info(f"Failed: {self.error_count}")
        logger.info(f"Total records inserted: {self.total_records_inserted}")
        logger.info(f"Average records per company: {self.total_records_inserted / max(self.success_count, 1):.1f}")
        logger.info("="*60)


async def main():
    """Main entry point for the backfill script"""
    parser = argparse.ArgumentParser(description="Backfill stock price historical data")
    parser.add_argument(
        "--tickers", 
        nargs="+", 
        help="Specific ticker symbols to backfill (e.g., --tickers 7203 9984)"
    )
    parser.add_argument(
        "--period",
        default="5y",
        help="Period to backfill (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y) [default: 5y]"
    )
    parser.add_argument(
        "--start-date",
        help="Start date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--end-date", 
        help="End date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of companies to process in each batch [default: 50]"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=10,
        help="Delay in seconds between batches [default: 10]"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without actually doing it"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No data will be inserted")
        # Show what would be processed
        async with StockPriceBackfiller(args.batch_size, args.delay) as backfiller:
            companies = await backfiller.get_companies_to_backfill(args.tickers)
            logger.info(f"Would process {len(companies)} companies:")
            for company in companies[:10]:  # Show first 10
                logger.info(f"  - {company.ticker_symbol}: {company.company_name_jp}")
            if len(companies) > 10:
                logger.info(f"  ... and {len(companies) - 10} more")
        return
    
    # Run the actual backfill
    async with StockPriceBackfiller(args.batch_size, args.delay) as backfiller:
        await backfiller.run_backfill(
            ticker_symbols=args.tickers,
            period=args.period,
            start_date=args.start_date,
            end_date=args.end_date
        )


if __name__ == "__main__":
    asyncio.run(main())