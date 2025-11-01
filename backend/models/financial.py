"""Financial Models"""

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class FinancialStatement(Base):
    """Financial Statement model"""

    __tablename__ = "financial_statements"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Period information
    fiscal_year = Column(Integer, nullable=False)
    fiscal_quarter = Column(Integer)  # 1, 2, 3, 4 or NULL for annual
    period_start = Column(Date)
    period_end = Column(Date, nullable=False)
    is_consolidated = Column(Boolean, default=True)
    
    # Income Statement (PL)
    revenue = Column(Float)
    cost_of_revenue = Column(Float)
    gross_profit = Column(Float)
    operating_expenses = Column(Float)
    operating_income = Column(Float)
    net_income = Column(Float)
    
    # Balance Sheet (BS)
    total_assets = Column(Float)
    current_assets = Column(Float)
    total_liabilities = Column(Float)
    current_liabilities = Column(Float)
    shareholders_equity = Column(Float)
    
    # Cash Flow (CF)
    operating_cash_flow = Column(Float)
    investing_cash_flow = Column(Float)
    financing_cash_flow = Column(Float)
    free_cash_flow = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class StockPrice(Base):
    """Stock Price model"""

    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    date = Column(Date, nullable=False, index=True)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    adjusted_close = Column(Float)
    volume = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())


class FinancialIndicator(Base):
    """Calculated Financial Indicators"""

    __tablename__ = "financial_indicators"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    
    # Valuation metrics
    per = Column(Float)  # Price to Earnings Ratio
    pbr = Column(Float)  # Price to Book Ratio
    psr = Column(Float)  # Price to Sales Ratio
    ev_ebitda = Column(Float)  # Enterprise Value to EBITDA
    
    # Profitability metrics
    roe = Column(Float)  # Return on Equity
    roa = Column(Float)  # Return on Assets
    gross_margin = Column(Float)
    operating_margin = Column(Float)
    net_margin = Column(Float)
    
    # Growth metrics
    revenue_growth_yoy = Column(Float)
    earnings_growth_yoy = Column(Float)
    
    # Financial health
    current_ratio = Column(Float)
    debt_to_equity = Column(Float)
    interest_coverage = Column(Float)
    
    # Dividend metrics
    dividend_yield = Column(Float)
    payout_ratio = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())