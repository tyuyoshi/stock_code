"""Company-related Pydantic schemas for API requests and responses"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CompanyBase(BaseModel):
    """Base company schema"""
    ticker_symbol: str = Field(..., min_length=4, max_length=10, description="Stock ticker symbol")
    company_name_jp: str = Field(..., min_length=1, max_length=255, description="Company name in Japanese")
    company_name_en: Optional[str] = Field(None, max_length=255, description="Company name in English")
    market_division: Optional[str] = Field(None, max_length=50, description="Market division (Prime, Standard, Growth)")
    industry_code: Optional[str] = Field(None, max_length=10, description="Industry code")
    industry_name: Optional[str] = Field(None, max_length=100, description="Industry name")


class CompanyCreate(CompanyBase):
    """Schema for company creation"""
    edinet_code: Optional[str] = Field(None, max_length=20, description="EDINET code")
    founding_date: Optional[datetime] = None
    listing_date: Optional[datetime] = None
    fiscal_year_end: Optional[str] = Field(None, max_length=10, description="Fiscal year end (MM-dd format)")
    employee_count: Optional[int] = Field(None, ge=0, description="Number of employees")
    description: Optional[str] = None
    website_url: Optional[str] = Field(None, max_length=255, description="Company website URL")
    headquarters_address: Optional[str] = None


class CompanyUpdate(BaseModel):
    """Schema for company updates"""
    company_name_jp: Optional[str] = Field(None, min_length=1, max_length=255)
    company_name_en: Optional[str] = Field(None, max_length=255)
    market_division: Optional[str] = Field(None, max_length=50)
    industry_code: Optional[str] = Field(None, max_length=10)
    industry_name: Optional[str] = Field(None, max_length=100)
    employee_count: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    website_url: Optional[str] = Field(None, max_length=255)
    headquarters_address: Optional[str] = None


class CompanyResponse(CompanyBase):
    """Schema for company response"""
    id: int
    edinet_code: Optional[str] = None
    founding_date: Optional[datetime] = None
    listing_date: Optional[datetime] = None
    fiscal_year_end: Optional[str] = None
    employee_count: Optional[int] = None
    market_cap: Optional[float] = None
    shares_outstanding: Optional[float] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    headquarters_address: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    """Schema for paginated company list response"""
    companies: List[CompanyResponse]
    total: int = Field(..., description="Total number of companies")
    page: int = Field(..., ge=1, description="Current page number")
    size: int = Field(..., ge=1, le=100, description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


class CompanySearchParams(BaseModel):
    """Schema for company search parameters"""
    q: Optional[str] = Field(None, description="Search query for company name or ticker")
    market_division: Optional[str] = Field(None, description="Filter by market division")
    industry_code: Optional[str] = Field(None, description="Filter by industry code")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")


class FinancialDataResponse(BaseModel):
    """Schema for company financial data response"""
    company_id: int
    financial_statements: List[dict] = Field(default_factory=list, description="Financial statements data")
    latest_period: Optional[str] = None
    currency: str = Field(default="JPY", description="Currency code")

    class Config:
        from_attributes = True


class FinancialIndicatorsResponse(BaseModel):
    """Schema for company financial indicators response"""
    company_id: int
    indicators: dict = Field(default_factory=dict, description="Financial indicators by category")
    date: Optional[datetime] = None
    period: Optional[str] = None

    class Config:
        from_attributes = True