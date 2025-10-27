"""Company Model"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.sql import func
from ..core.database import Base


class Company(Base):
    """Company model"""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    ticker_symbol = Column(String(10), unique=True, index=True, nullable=False)
    edinet_code = Column(String(20), unique=True, index=True)
    company_name_jp = Column(String(255), nullable=False)
    company_name_en = Column(String(255))
    
    # Market information
    market_division = Column(String(50))  # Prime, Standard, Growth
    industry_code = Column(String(10))
    industry_name = Column(String(100))
    
    # Company details
    founding_date = Column(DateTime)
    listing_date = Column(DateTime)
    fiscal_year_end = Column(String(10))  # e.g., "03-31"
    employee_count = Column(Integer)
    
    # Financial summary
    market_cap = Column(Float)
    shares_outstanding = Column(Float)
    
    # Metadata
    description = Column(Text)
    website_url = Column(String(255))
    headquarters_address = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())