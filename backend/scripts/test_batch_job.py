#!/usr/bin/env python
"""Test script for batch job functionality"""

import asyncio
import logging
import sys
import os
from datetime import datetime, date

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.trading_calendar import TradingCalendar, is_trading_day
from services.notification import NotificationService, BatchJobResult, NotificationLevel
from batch.daily_update import DailyUpdateJob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_trading_calendar():
    """Test trading calendar functionality"""
    print("=== Testing Trading Calendar ===")
    
    calendar = TradingCalendar()
    today = date.today()
    
    print(f"Today ({today}): {is_trading_day()}")
    print(f"Next trading day: {calendar.get_next_trading_day()}")
    print(f"Previous trading day: {calendar.get_previous_trading_day()}")
    
    # Test holidays for current year
    holidays = calendar.get_holidays(today.year)
    print(f"\nHolidays in {today.year} ({len(holidays)} total):")
    for holiday in sorted(holidays[:10], key=lambda h: h.date):  # Show first 10
        print(f"  {holiday.date}: {holiday.name}")
    if len(holidays) > 10:
        print(f"  ... and {len(holidays) - 10} more holidays")
    
    # Test specific dates
    test_dates = [
        date(2024, 1, 1),   # New Year
        date(2024, 5, 3),   # Constitution Day
        date(2024, 12, 25), # Christmas (not a Japanese holiday)
        date(2024, 12, 29), # Year-end holiday
    ]
    
    print(f"\nTest specific dates:")
    for test_date in test_dates:
        is_trading = calendar.is_trading_day(test_date)
        print(f"  {test_date}: {'Trading day' if is_trading else 'Not trading day'}")


def test_notification_service():
    """Test notification service"""
    print("\n=== Testing Notification Service ===")
    
    notification_service = NotificationService()
    
    # Create test batch result
    test_result = BatchJobResult(
        job_name="Test Batch Job",
        start_time=datetime.now(),
        end_time=datetime.now(),
        status="success",
        total_items=100,
        successful_items=95,
        failed_items=5,
        error_messages=["Sample error 1", "Sample error 2"],
        execution_time_seconds=120.5
    )
    
    print(f"Test result created:")
    print(f"  Job: {test_result.job_name}")
    print(f"  Status: {test_result.status}")
    print(f"  Success rate: {test_result.success_rate:.1f}%")
    print(f"  Execution time: {test_result.execution_time_seconds}s")
    
    # Test notification (will only work if configured)
    try:
        notification_service.notify_batch_result(test_result, NotificationLevel.INFO)
        print("✅ Notification sent successfully")
    except Exception as e:
        print(f"⚠️ Notification failed (expected if not configured): {e}")


async def test_daily_update_job():
    """Test daily update job (dry run)"""
    print("\n=== Testing Daily Update Job (Dry Run) ===")
    
    try:
        # Check if today is a trading day first
        if not is_trading_day():
            print("⚠️ Today is not a trading day - job would be skipped")
            return
        
        print("✅ Today is a trading day - job would proceed")
        
        # Initialize job (don't run it fully)
        job = DailyUpdateJob()
        
        # Test company retrieval
        companies = job.get_active_companies()
        print(f"📊 Found {len(companies)} companies in database")
        
        if companies:
            sample_company = companies[0]
            print(f"📈 Sample company: {sample_company.company_name} ({sample_company.ticker_symbol})")
        
        print("✅ Daily update job structure is valid")
        
    except Exception as e:
        print(f"❌ Daily update job test failed: {e}")
        logger.exception("Daily update job test error")
    finally:
        # Ensure database connection is closed
        if 'job' in locals():
            job.db.close()


def test_cron_setup():
    """Test cron setup and configuration"""
    print("\n=== Testing Cron Setup ===")
    
    # Check if crontab file exists
    crontab_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "infrastructure", "docker", "crontab"
    )
    
    if os.path.exists(crontab_path):
        print("✅ Crontab file exists")
        with open(crontab_path, 'r') as f:
            content = f.read()
            print(f"📄 Crontab content:\n{content}")
    else:
        print("❌ Crontab file not found")
    
    # Check if shell script exists
    script_path = os.path.join(
        os.path.dirname(__file__),
        "run_daily_update.sh"
    )
    
    if os.path.exists(script_path):
        print("✅ Daily update shell script exists")
        print(f"📝 Script path: {script_path}")
        
        # Check if script is executable
        if os.access(script_path, os.X_OK):
            print("✅ Script is executable")
        else:
            print("⚠️ Script is not executable (run: chmod +x)")
    else:
        print("❌ Daily update shell script not found")


async def main():
    """Main test function"""
    print("🧪 Stock Code Batch Job Test Suite")
    print("=" * 50)
    
    # Run all tests
    test_trading_calendar()
    test_notification_service()
    await test_daily_update_job()
    test_cron_setup()
    
    print("\n" + "=" * 50)
    print("🏁 Test suite completed")
    
    # Instructions for manual testing
    print("\n📋 Manual Testing Instructions:")
    print("1. Start scheduler service:")
    print("   docker compose --profile scheduler up -d")
    print("\n2. Check logs:")
    print("   docker compose logs -f scheduler")
    print("\n3. Test manual execution:")
    print("   cd backend && python -m batch.daily_update")
    print("\n4. Test trading calendar:")
    print("   cd backend && python services/trading_calendar.py")
    print("\n5. Test notification:")
    print("   cd backend && python services/notification.py")


if __name__ == "__main__":
    asyncio.run(main())