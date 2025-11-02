"""Yahoo Finance API Client for Stock Price Data"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import yfinance as yf
from redis import Redis

try:
    from ..core.config import settings
except ImportError:
    from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """Client for fetching stock data from Yahoo Finance"""

    def __init__(self, redis_client: Optional[Redis] = None):
        """Initialize Yahoo Finance client
        
        Args:
            redis_client: Redis client for caching (optional)
        """
        self.redis_client = redis_client
        self.cache_ttl = 300  # 5 minutes cache for real-time data
        self.rate_limit_delay = 0.5  # 500ms between requests
        
    def _format_ticker(self, ticker_symbol: str) -> str:
        """Format ticker symbol for Japanese stocks
        
        Args:
            ticker_symbol: Raw ticker symbol (e.g., "7203")
            
        Returns:
            Formatted ticker for Yahoo Finance (e.g., "7203.T")
        """
        if not ticker_symbol.endswith('.T'):
            return f"{ticker_symbol}.T"
        return ticker_symbol
    
    def _get_cache_key(self, ticker: str, data_type: str) -> str:
        """Generate cache key for Redis
        
        Args:
            ticker: Stock ticker symbol
            data_type: Type of data (e.g., 'price', 'info', 'history')
            
        Returns:
            Cache key string
        """
        return f"yahoo_finance:{ticker}:{data_type}"
    
    async def _get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from Redis cache
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached data or None if not found
        """
        if not self.redis_client:
            return None
            
        try:
            import json
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Failed to get cached data: {e}")
        
        return None
    
    async def _set_cached_data(self, cache_key: str, data: Dict[str, Any], ttl: int = None) -> None:
        """Set data in Redis cache
        
        Args:
            cache_key: Cache key
            data: Data to cache
            ttl: Time to live in seconds (defaults to self.cache_ttl)
        """
        if not self.redis_client:
            return
            
        try:
            import json
            self.redis_client.setex(
                cache_key, 
                ttl or self.cache_ttl, 
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.warning(f"Failed to cache data: {e}")
    
    async def get_stock_price(self, ticker_symbol: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get current stock price data
        
        Args:
            ticker_symbol: Stock ticker symbol
            use_cache: Whether to use cache
            
        Returns:
            Dictionary containing current price data or None if failed
        """
        formatted_ticker = self._format_ticker(ticker_symbol)
        cache_key = self._get_cache_key(formatted_ticker, "price")
        
        # Check cache first
        if use_cache:
            cached_data = await self._get_cached_data(cache_key)
            if cached_data:
                logger.debug(f"Using cached price data for {formatted_ticker}")
                return cached_data
        
        try:
            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)
            
            # Fetch data from Yahoo Finance
            ticker = yf.Ticker(formatted_ticker)
            info = ticker.info
            
            # Get latest trading day data
            hist = ticker.history(period="2d")  # Get last 2 days to ensure we have data
            
            if hist.empty:
                logger.warning(f"No historical data found for {formatted_ticker}")
                return None
                
            latest = hist.iloc[-1]  # Get the most recent day
            
            price_data = {
                "ticker": ticker_symbol,
                "formatted_ticker": formatted_ticker,
                "date": latest.name.strftime('%Y-%m-%d'),
                "open_price": float(latest['Open']) if pd.notna(latest['Open']) else None,
                "high_price": float(latest['High']) if pd.notna(latest['High']) else None,
                "low_price": float(latest['Low']) if pd.notna(latest['Low']) else None,
                "close_price": float(latest['Close']) if pd.notna(latest['Close']) else None,
                "volume": float(latest['Volume']) if pd.notna(latest['Volume']) else None,
                "previous_close": info.get('previousClose'),
                "market_cap": info.get('marketCap'),
                "currency": info.get('currency', 'JPY'),
                "updated_at": datetime.now().isoformat()
            }
            
            # Cache the data
            if use_cache:
                await self._set_cached_data(cache_key, price_data)
            
            logger.info(f"Successfully fetched price data for {formatted_ticker}")
            return price_data
            
        except Exception as e:
            logger.error(f"Failed to fetch price data for {formatted_ticker}: {e}")
            return None
    
    async def get_historical_data(
        self, 
        ticker_symbol: str, 
        period: str = "5y",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """Get historical stock price data
        
        Args:
            ticker_symbol: Stock ticker symbol
            period: Period to fetch (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            
        Returns:
            List of historical price data dictionaries or None if failed
        """
        formatted_ticker = self._format_ticker(ticker_symbol)
        
        try:
            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)
            
            # Fetch historical data
            ticker = yf.Ticker(formatted_ticker)
            
            if start_date and end_date:
                hist = ticker.history(start=start_date, end=end_date)
            else:
                hist = ticker.history(period=period)
            
            if hist.empty:
                logger.warning(f"No historical data found for {formatted_ticker}")
                return None
            
            # Convert to list of dictionaries
            historical_data = []
            for date, row in hist.iterrows():
                historical_data.append({
                    "ticker": ticker_symbol,
                    "date": date.strftime('%Y-%m-%d'),
                    "open_price": float(row['Open']) if pd.notna(row['Open']) else None,
                    "high_price": float(row['High']) if pd.notna(row['High']) else None,
                    "low_price": float(row['Low']) if pd.notna(row['Low']) else None,
                    "close_price": float(row['Close']) if pd.notna(row['Close']) else None,
                    "volume": float(row['Volume']) if pd.notna(row['Volume']) else None,
                })
            
            logger.info(f"Successfully fetched {len(historical_data)} historical records for {formatted_ticker}")
            return historical_data
            
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {formatted_ticker}: {e}")
            return None
    
    async def get_company_info(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """Get company information from Yahoo Finance
        
        Args:
            ticker_symbol: Stock ticker symbol
            
        Returns:
            Dictionary containing company information or None if failed
        """
        formatted_ticker = self._format_ticker(ticker_symbol)
        cache_key = self._get_cache_key(formatted_ticker, "info")
        
        # Check cache (longer TTL for company info)
        cached_data = await self._get_cached_data(cache_key)
        if cached_data:
            logger.debug(f"Using cached company info for {formatted_ticker}")
            return cached_data
        
        try:
            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)
            
            # Fetch company info
            ticker = yf.Ticker(formatted_ticker)
            info = ticker.info
            
            company_info = {
                "ticker": ticker_symbol,
                "formatted_ticker": formatted_ticker,
                "company_name": info.get('longName', info.get('shortName')),
                "industry": info.get('industry'),
                "sector": info.get('sector'),
                "market_cap": info.get('marketCap'),
                "shares_outstanding": info.get('sharesOutstanding'),
                "currency": info.get('currency', 'JPY'),
                "exchange": info.get('exchange'),
                "website": info.get('website'),
                "description": info.get('longBusinessSummary'),
                "employee_count": info.get('fullTimeEmployees'),
                "updated_at": datetime.now().isoformat()
            }
            
            # Cache with longer TTL (1 day for company info)
            await self._set_cached_data(cache_key, company_info, ttl=86400)
            
            logger.info(f"Successfully fetched company info for {formatted_ticker}")
            return company_info
            
        except Exception as e:
            logger.error(f"Failed to fetch company info for {formatted_ticker}: {e}")
            return None
    
    async def get_dividends(self, ticker_symbol: str, period: str = "2y") -> Optional[List[Dict[str, Any]]]:
        """Get dividend information
        
        Args:
            ticker_symbol: Stock ticker symbol
            period: Period to fetch dividends
            
        Returns:
            List of dividend data dictionaries or None if failed
        """
        formatted_ticker = self._format_ticker(ticker_symbol)
        
        try:
            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)
            
            # Fetch dividend data
            ticker = yf.Ticker(formatted_ticker)
            dividends = ticker.dividends
            
            if dividends.empty:
                logger.info(f"No dividend data found for {formatted_ticker}")
                return []
            
            # Filter by period if needed
            if period != "max":
                end_date = datetime.now()
                if period.endswith('y'):
                    years = int(period[:-1])
                    start_date = end_date - timedelta(days=years * 365)
                elif period.endswith('mo'):
                    months = int(period[:-2])
                    start_date = end_date - timedelta(days=months * 30)
                else:
                    start_date = end_date - timedelta(days=365)  # Default to 1 year
                
                dividends = dividends[dividends.index >= start_date]
            
            # Convert to list of dictionaries
            dividend_data = []
            for date, amount in dividends.items():
                dividend_data.append({
                    "ticker": ticker_symbol,
                    "ex_date": date.strftime('%Y-%m-%d'),
                    "dividend_amount": float(amount),
                })
            
            logger.info(f"Successfully fetched {len(dividend_data)} dividend records for {formatted_ticker}")
            return dividend_data
            
        except Exception as e:
            logger.error(f"Failed to fetch dividend data for {formatted_ticker}: {e}")
            return None
    
    async def get_stock_splits(self, ticker_symbol: str, period: str = "5y") -> Optional[List[Dict[str, Any]]]:
        """Get stock split information
        
        Args:
            ticker_symbol: Stock ticker symbol
            period: Period to fetch splits
            
        Returns:
            List of stock split data dictionaries or None if failed
        """
        formatted_ticker = self._format_ticker(ticker_symbol)
        
        try:
            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)
            
            # Fetch stock split data
            ticker = yf.Ticker(formatted_ticker)
            splits = ticker.splits
            
            if splits.empty:
                logger.info(f"No stock split data found for {formatted_ticker}")
                return []
            
            # Convert to list of dictionaries
            split_data = []
            for date, ratio in splits.items():
                split_data.append({
                    "ticker": ticker_symbol,
                    "split_date": date.strftime('%Y-%m-%d'),
                    "split_ratio": float(ratio),
                })
            
            logger.info(f"Successfully fetched {len(split_data)} stock split records for {formatted_ticker}")
            return split_data
            
        except Exception as e:
            logger.error(f"Failed to fetch stock split data for {formatted_ticker}: {e}")
            return None
    
    async def bulk_fetch_prices(self, ticker_symbols: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Fetch current prices for multiple tickers in parallel
        
        Args:
            ticker_symbols: List of ticker symbols
            
        Returns:
            Dictionary mapping ticker symbols to price data
        """
        logger.info(f"Bulk fetching prices for {len(ticker_symbols)} tickers")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
        
        async def fetch_with_semaphore(ticker: str):
            async with semaphore:
                return ticker, await self.get_stock_price(ticker)
        
        # Execute all requests concurrently
        tasks = [fetch_with_semaphore(ticker) for ticker in ticker_symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        price_data = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in bulk fetch: {result}")
                continue
            
            ticker, data = result
            price_data[ticker] = data
        
        logger.info(f"Successfully fetched prices for {len([v for v in price_data.values() if v])} out of {len(ticker_symbols)} tickers")
        return price_data