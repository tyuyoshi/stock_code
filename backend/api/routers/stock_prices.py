"""Stock Prices API Endpoints"""

from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.database import get_db
from models.company import Company
from models.financial import StockPrice
from services.yahoo_finance_client import YahooFinanceClient
from core.dependencies import get_yahoo_finance_client
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/stock-prices", tags=["stock-prices"])


# Pydantic models for response
class StockPriceResponse(BaseModel):
    """Stock price response model"""
    id: int
    company_id: int
    ticker_symbol: str
    date: date
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    close_price: Optional[float] = None
    adjusted_close: Optional[float] = None
    volume: Optional[float] = None
    data_source: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LatestPriceResponse(BaseModel):
    """Latest price response model"""
    ticker_symbol: str
    current_price: Optional[float] = None
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    volume: Optional[float] = None
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    market_cap: Optional[float] = None
    currency: str = "JPY"
    last_updated: datetime


class ChartDataPoint(BaseModel):
    """Chart data point model"""
    date: date
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None


class ChartDataResponse(BaseModel):
    """Chart data response model"""
    ticker_symbol: str
    period: str
    data: List[ChartDataPoint]
    data_source: str = "database"


@router.get("/{ticker}/latest", response_model=LatestPriceResponse)
async def get_latest_stock_price(
    ticker: str,
    live: bool = Query(False, description="Fetch live data from Yahoo Finance"),
    db: Session = Depends(get_db),
    yahoo_client: YahooFinanceClient = Depends(get_yahoo_finance_client)
):
    """Get latest stock price for a ticker"""
    
    # Verify ticker exists
    company = db.query(Company).filter(Company.ticker_symbol == ticker).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company with ticker {ticker} not found")
    
    if live:
        # Fetch live data from Yahoo Finance
        try:
            price_data = await yahoo_client.get_stock_price(ticker, use_cache=False)
            if not price_data:
                raise HTTPException(status_code=503, detail="Unable to fetch live price data from Yahoo Finance. The market may be closed or the ticker may be invalid.")
            
            # Calculate change if we have previous close
            current_price = price_data.get('close_price')
            previous_close = price_data.get('previous_close')
            change = None
            change_percent = None
            
            if current_price and previous_close:
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100
            
            return LatestPriceResponse(
                ticker_symbol=ticker,
                current_price=current_price,
                open_price=price_data.get('open_price'),
                high_price=price_data.get('high_price'),
                low_price=price_data.get('low_price'),
                volume=price_data.get('volume'),
                previous_close=previous_close,
                change=change,
                change_percent=change_percent,
                market_cap=price_data.get('market_cap'),
                currency=price_data.get('currency', 'JPY'),
                last_updated=datetime.now()
            )
        except HTTPException:
            raise  # Re-raise HTTPExceptions as-is
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error fetching live data for {ticker}: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Error fetching live data: {str(e)}")
    
    # Get latest price from database
    latest_price = db.query(StockPrice).filter(
        StockPrice.company_id == company.id
    ).order_by(desc(StockPrice.date)).first()
    
    if not latest_price:
        raise HTTPException(status_code=404, detail=f"No price data found for {ticker}")
    
    # Get previous day's price for change calculation
    previous_price = db.query(StockPrice).filter(
        StockPrice.company_id == company.id,
        StockPrice.date < latest_price.date
    ).order_by(desc(StockPrice.date)).first()
    
    change = None
    change_percent = None
    if latest_price.close_price and previous_price and previous_price.close_price:
        change = latest_price.close_price - previous_price.close_price
        change_percent = (change / previous_price.close_price) * 100
    
    return LatestPriceResponse(
        ticker_symbol=ticker,
        current_price=latest_price.close_price,
        open_price=latest_price.open_price,
        high_price=latest_price.high_price,
        low_price=latest_price.low_price,
        volume=latest_price.volume,
        previous_close=previous_price.close_price if previous_price else None,
        change=change,
        change_percent=change_percent,
        currency="JPY",
        last_updated=latest_price.date
    )


@router.get("/{ticker}/historical", response_model=List[StockPriceResponse])
async def get_historical_stock_prices(
    ticker: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get historical stock prices for a ticker"""
    
    # Verify ticker exists
    company = db.query(Company).filter(Company.ticker_symbol == ticker).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company with ticker {ticker} not found")
    
    # Build query
    query = db.query(StockPrice).filter(StockPrice.company_id == company.id)
    
    # Apply date filters
    if start_date and end_date:
        query = query.filter(
            StockPrice.date >= start_date,
            StockPrice.date <= end_date
        )
    elif start_date:
        query = query.filter(StockPrice.date >= start_date)
    elif end_date:
        query = query.filter(StockPrice.date <= end_date)
    else:
        # Default to last N days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        query = query.filter(
            StockPrice.date >= start_date,
            StockPrice.date <= end_date
        )
    
    # Execute query
    prices = query.order_by(desc(StockPrice.date)).all()
    
    if not prices:
        raise HTTPException(
            status_code=404, 
            detail=f"No historical price data found for {ticker} in the specified period"
        )
    
    # Convert to response model
    response_data = []
    for price in prices:
        response_data.append(StockPriceResponse(
            id=price.id,
            company_id=price.company_id,
            ticker_symbol=ticker,
            date=price.date,
            open_price=price.open_price,
            high_price=price.high_price,
            low_price=price.low_price,
            close_price=price.close_price,
            adjusted_close=price.adjusted_close,
            volume=price.volume,
            data_source=price.data_source,
            created_at=price.created_at
        ))
    
    return response_data


@router.get("/{ticker}/chart", response_model=ChartDataResponse)
async def get_chart_data(
    ticker: str,
    period: str = Query("1mo", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y)$", description="Chart period"),
    db: Session = Depends(get_db)
):
    """Get chart data for a ticker"""
    
    # Verify ticker exists
    company = db.query(Company).filter(Company.ticker_symbol == ticker).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company with ticker {ticker} not found")
    
    # Calculate date range based on period
    end_date = datetime.now().date()
    
    period_days = {
        "1d": 1,
        "5d": 5,
        "1mo": 30,
        "3mo": 90,
        "6mo": 180,
        "1y": 365,
        "2y": 730,
        "5y": 1825
    }
    
    days = period_days.get(period, 30)
    start_date = end_date - timedelta(days=days)
    
    # Get price data
    prices = db.query(StockPrice).filter(
        StockPrice.company_id == company.id,
        StockPrice.date >= start_date,
        StockPrice.date <= end_date
    ).order_by(StockPrice.date).all()
    
    if not prices:
        raise HTTPException(
            status_code=404,
            detail=f"No chart data found for {ticker} in period {period}"
        )
    
    # Convert to chart data points
    chart_data = []
    for price in prices:
        chart_data.append(ChartDataPoint(
            date=price.date,
            open=price.open_price,
            high=price.high_price,
            low=price.low_price,
            close=price.close_price,
            volume=price.volume
        ))
    
    return ChartDataResponse(
        ticker_symbol=ticker,
        period=period,
        data=chart_data
    )


@router.get("/", response_model=List[StockPriceResponse])
async def get_stock_prices(
    tickers: List[str] = Query(..., description="List of ticker symbols"),
    latest_only: bool = Query(True, description="Return only latest price for each ticker"),
    db: Session = Depends(get_db)
):
    """Get stock prices for multiple tickers"""
    
    if len(tickers) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 tickers allowed per request")
    
    # Get company IDs
    companies = db.query(Company).filter(Company.ticker_symbol.in_(tickers)).all()
    company_map = {company.ticker_symbol: company for company in companies}
    
    missing_tickers = set(tickers) - set(company_map.keys())
    if missing_tickers:
        raise HTTPException(
            status_code=404,
            detail=f"Companies not found for tickers: {list(missing_tickers)}"
        )
    
    # Get price data
    company_ids = [company.id for company in companies]
    query = db.query(StockPrice).filter(StockPrice.company_id.in_(company_ids))
    
    if latest_only:
        # Get latest price for each company using efficient window function
        from sqlalchemy import func, and_
        
        # Subquery to get latest date for each company
        latest_dates_subq = db.query(
            StockPrice.company_id,
            func.max(StockPrice.date).label('latest_date')
        ).filter(
            StockPrice.company_id.in_(company_ids)
        ).group_by(StockPrice.company_id).subquery()
        
        # Join with original table to get complete records
        prices = db.query(StockPrice).join(
            latest_dates_subq,
            and_(
                StockPrice.company_id == latest_dates_subq.c.company_id,
                StockPrice.date == latest_dates_subq.c.latest_date
            )
        ).all()
    else:
        prices = query.order_by(desc(StockPrice.date)).all()
    
    # Create efficient company lookup
    company_lookup = {company.id: company.ticker_symbol for company in companies}
    
    # Convert to response model
    response_data = []
    for price in prices:
        ticker = company_lookup.get(price.company_id)
        if ticker:
            response_data.append(StockPriceResponse(
                id=price.id,
                company_id=price.company_id,
                ticker_symbol=ticker,
                date=price.date,
                open_price=price.open_price,
                high_price=price.high_price,
                low_price=price.low_price,
                close_price=price.close_price,
                adjusted_close=price.adjusted_close,
                volume=price.volume,
                data_source=price.data_source,
                created_at=price.created_at
            ))
    
    return response_data