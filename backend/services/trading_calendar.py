"""Trading Calendar Service for Japanese Stock Market"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Optional
import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Holiday:
    """Represents a Japanese holiday"""
    date: date
    name: str
    name_en: str


class TradingCalendar:
    """Japanese stock market trading calendar service"""
    
    # Known market holidays (can be extended)
    FIXED_HOLIDAYS = [
        # New Year holidays
        ("01-01", "元日", "New Year's Day"),
        ("01-02", "休日", "Bank Holiday"),
        ("01-03", "休日", "Bank Holiday"),
        
        # Golden Week
        ("04-29", "昭和の日", "Showa Day"),
        ("05-03", "憲法記念日", "Constitution Day"),
        ("05-04", "みどりの日", "Greenery Day"),
        ("05-05", "こどもの日", "Children's Day"),
        
        # Other fixed holidays
        ("02-11", "建国記念の日", "National Foundation Day"),
        ("02-23", "天皇誕生日", "Emperor's Birthday"),
        ("03-21", "春分の日", "Spring Equinox"), # Approximate
        ("07-20", "海の日", "Marine Day"), # 3rd Monday in July
        ("08-11", "山の日", "Mountain Day"),
        ("09-23", "秋分の日", "Autumn Equinox"), # Approximate
        ("10-10", "スポーツの日", "Sports Day"), # 2nd Monday in October
        ("11-03", "文化の日", "Culture Day"),
        ("11-23", "勤労感謝の日", "Labor Thanksgiving Day"),
        ("12-29", "休日", "Year-end Holiday"),
        ("12-30", "休日", "Year-end Holiday"),
        ("12-31", "休日", "Year-end Holiday"),
    ]
    
    def __init__(self):
        self.cache: dict[int, List[Holiday]] = {}
    
    def is_trading_day(self, target_date: Optional[date] = None) -> bool:
        """
        Check if the given date is a trading day
        
        Args:
            target_date: Date to check (defaults to today)
            
        Returns:
            True if it's a trading day, False otherwise
        """
        if target_date is None:
            target_date = date.today()
        
        # Weekend check
        if target_date.weekday() >= 5:  # Saturday=5, Sunday=6
            logger.debug(f"{target_date} is weekend, not a trading day")
            return False
        
        # Holiday check
        if self.is_holiday(target_date):
            logger.debug(f"{target_date} is a holiday, not a trading day")
            return False
        
        logger.debug(f"{target_date} is a trading day")
        return True
    
    def is_holiday(self, target_date: date) -> bool:
        """Check if the given date is a Japanese holiday"""
        holidays = self.get_holidays(target_date.year)
        return target_date in [h.date for h in holidays]
    
    def get_holidays(self, year: int) -> List[Holiday]:
        """Get list of holidays for the given year"""
        if year in self.cache:
            return self.cache[year]
        
        holidays = []
        
        # Add fixed holidays
        for month_day, name, name_en in self.FIXED_HOLIDAYS:
            try:
                month, day = map(int, month_day.split('-'))
                holiday_date = date(year, month, day)
                holidays.append(Holiday(holiday_date, name, name_en))
            except ValueError:
                continue
        
        # Add calculated holidays (moving holidays)
        holidays.extend(self._get_moving_holidays(year))
        
        # Remove holidays that fall on weekends (and add substitute holidays)
        holidays = self._adjust_weekend_holidays(holidays)
        
        # Cache the result
        self.cache[year] = holidays
        logger.info(f"Loaded {len(holidays)} holidays for {year}")
        
        return holidays
    
    def _get_moving_holidays(self, year: int) -> List[Holiday]:
        """Get holidays that change dates each year"""
        holidays = []
        
        try:
            # Coming of Age Day (2nd Monday in January)
            holidays.append(self._get_nth_weekday(year, 1, 1, 2, "成人の日", "Coming of Age Day"))
            
            # Marine Day (3rd Monday in July, except Olympics years)
            if year == 2020:
                holidays.append(Holiday(date(2020, 7, 23), "海の日", "Marine Day"))
            elif year == 2021:
                holidays.append(Holiday(date(2021, 7, 22), "海の日", "Marine Day"))
            else:
                holidays.append(self._get_nth_weekday(year, 7, 1, 3, "海の日", "Marine Day"))
            
            # Sports Day (2nd Monday in October, except Olympics years)
            if year == 2020:
                holidays.append(Holiday(date(2020, 7, 24), "スポーツの日", "Sports Day"))
            elif year == 2021:
                holidays.append(Holiday(date(2021, 7, 23), "スポーツの日", "Sports Day"))
            else:
                holidays.append(self._get_nth_weekday(year, 10, 1, 2, "スポーツの日", "Sports Day"))
            
        except Exception as e:
            logger.warning(f"Error calculating moving holidays for {year}: {e}")
        
        return holidays
    
    def _get_nth_weekday(self, year: int, month: int, weekday: int, n: int, name: str, name_en: str) -> Holiday:
        """Get the nth occurrence of a weekday in a month"""
        first_day = date(year, month, 1)
        first_weekday = first_day.weekday()
        
        # Calculate the date of the first occurrence
        days_to_add = (weekday - first_weekday) % 7
        first_occurrence = first_day + timedelta(days=days_to_add)
        
        # Add weeks to get the nth occurrence
        nth_occurrence = first_occurrence + timedelta(weeks=n-1)
        
        return Holiday(nth_occurrence, name, name_en)
    
    def _adjust_weekend_holidays(self, holidays: List[Holiday]) -> List[Holiday]:
        """Adjust holidays that fall on weekends and add substitute holidays"""
        adjusted_holidays = []
        
        for holiday in holidays:
            adjusted_holidays.append(holiday)
            
            # If holiday falls on Sunday, add substitute holiday on Monday
            if holiday.date.weekday() == 6:  # Sunday
                substitute_date = holiday.date + timedelta(days=1)
                substitute_holiday = Holiday(
                    substitute_date,
                    f"{holiday.name}(振替休日)",
                    f"{holiday.name_en} (Substitute)"
                )
                adjusted_holidays.append(substitute_holiday)
                logger.debug(f"Added substitute holiday for {holiday.name} on {substitute_date}")
            
            # If holiday falls on Saturday, add substitute holiday on Monday
            elif holiday.date.weekday() == 5:  # Saturday
                substitute_date = holiday.date + timedelta(days=2)
                substitute_holiday = Holiday(
                    substitute_date,
                    f"{holiday.name}(振替休日)",
                    f"{holiday.name_en} (Substitute)"
                )
                adjusted_holidays.append(substitute_holiday)
                logger.debug(f"Added substitute holiday for {holiday.name} on {substitute_date}")
        
        return adjusted_holidays
    
    def get_next_trading_day(self, from_date: Optional[date] = None) -> date:
        """Get the next trading day from the given date"""
        if from_date is None:
            from_date = date.today()
        
        next_day = from_date + timedelta(days=1)
        while not self.is_trading_day(next_day):
            next_day += timedelta(days=1)
        
        return next_day
    
    def get_previous_trading_day(self, from_date: Optional[date] = None) -> date:
        """Get the previous trading day from the given date"""
        if from_date is None:
            from_date = date.today()
        
        prev_day = from_date - timedelta(days=1)
        while not self.is_trading_day(prev_day):
            prev_day -= timedelta(days=1)
        
        return prev_day
    
    def get_trading_days_in_range(self, start_date: date, end_date: date) -> List[date]:
        """Get all trading days in the given date range"""
        trading_days = []
        current_date = start_date
        
        while current_date <= end_date:
            if self.is_trading_day(current_date):
                trading_days.append(current_date)
            current_date += timedelta(days=1)
        
        return trading_days


# Global instance
trading_calendar = TradingCalendar()


def is_trading_day(target_date: Optional[date] = None) -> bool:
    """Convenience function to check if a date is a trading day"""
    return trading_calendar.is_trading_day(target_date)


def get_next_trading_day(from_date: Optional[date] = None) -> date:
    """Convenience function to get the next trading day"""
    return trading_calendar.get_next_trading_day(from_date)


def get_previous_trading_day(from_date: Optional[date] = None) -> date:
    """Convenience function to get the previous trading day"""
    return trading_calendar.get_previous_trading_day(from_date)


if __name__ == "__main__":
    # Test the trading calendar
    logging.basicConfig(level=logging.INFO)
    
    today = date.today()
    print(f"Today ({today}) is trading day: {is_trading_day()}")
    print(f"Next trading day: {get_next_trading_day()}")
    print(f"Previous trading day: {get_previous_trading_day()}")
    
    # Test holidays for current year
    holidays = trading_calendar.get_holidays(today.year)
    print(f"\nHolidays in {today.year}:")
    for holiday in sorted(holidays, key=lambda h: h.date):
        print(f"  {holiday.date}: {holiday.name} ({holiday.name_en})")