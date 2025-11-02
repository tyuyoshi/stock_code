"""Company API endpoints"""

import math
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.rate_limiter import limiter, RateLimits
from services.company_service import CompanyService
from schemas.company import (
    CompanyResponse,
    CompanyListResponse,
    CompanySearchParams,
    CompanyCreate,
    CompanyUpdate,
    FinancialDataResponse,
    FinancialIndicatorsResponse
)

router = APIRouter(
    prefix="/api/v1/companies",
    tags=["companies"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=CompanyListResponse)
@limiter.limit(RateLimits.STANDARD)
async def get_companies(
    request: Request,
    q: str = Query(None, description="Search query for company name or ticker"),
    market_division: str = Query(None, description="Filter by market division"),
    industry_code: str = Query(None, description="Filter by industry code"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    Get companies with search and pagination.
    
    - **q**: Search in company name (JP/EN) or ticker symbol
    - **market_division**: Filter by market division (Prime, Standard, Growth)
    - **industry_code**: Filter by industry code
    - **page**: Page number (starting from 1)
    - **size**: Number of companies per page (max 100)
    """
    search_params = CompanySearchParams(
        q=q,
        market_division=market_division,
        industry_code=industry_code,
        page=page,
        size=size
    )
    
    companies, total = CompanyService.get_companies(db, search_params)
    total_pages = math.ceil(total / size) if total > 0 else 0
    
    return CompanyListResponse(
        companies=companies,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


@router.get("/{company_id}", response_model=CompanyResponse)
@limiter.limit(RateLimits.STANDARD)
async def get_company(
    request: Request,
    company_id: int,
    db: Session = Depends(get_db)
):
    """
    Get company details by ID.
    
    Returns comprehensive company information including:
    - Basic company data (name, ticker, industry)
    - Market information (division, market cap)
    - Company details (founding date, employees)
    - Contact information (website, headquarters)
    """
    company = CompanyService.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return company


@router.get("/{company_id}/financials", response_model=FinancialDataResponse)
@limiter.limit(RateLimits.STANDARD)
async def get_company_financials(
    request: Request,
    company_id: int,
    limit: int = Query(5, ge=1, le=20, description="Number of periods to return"),
    db: Session = Depends(get_db)
):
    """
    Get company's financial statements data.
    
    Returns financial statements for the specified company:
    - Income statement (revenue, operating income, net income)
    - Balance sheet (assets, equity, liabilities)
    - Cash flow statement (operating, investing, financing CF)
    
    Data is returned in descending order by period (most recent first).
    """
    return CompanyService.get_company_financials(db, company_id, limit)


@router.get("/{company_id}/indicators", response_model=FinancialIndicatorsResponse)
@limiter.limit(RateLimits.STANDARD)
async def get_company_indicators(
    request: Request,
    company_id: int,
    db: Session = Depends(get_db)
):
    """
    Get company's financial indicators.
    
    Returns calculated financial indicators organized by category:
    - **Profitability**: ROE, ROA, margins
    - **Safety**: Equity ratio, debt ratios, liquidity ratios
    - **Efficiency**: Asset turnover, inventory turnover
    - **Growth**: Revenue, income, asset growth rates
    - **Valuation**: P/E, P/B, P/CF ratios
    - **Cash Flow**: Operating CF margin, free cash flow ratios
    """
    return CompanyService.get_company_indicators(db, company_id)


@router.post("/", response_model=CompanyResponse, status_code=201)
@limiter.limit(RateLimits.STRICT)
async def create_company(
    request: Request,
    company_data: CompanyCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new company.
    
    **Note**: This endpoint is rate-limited more strictly as it modifies data.
    """
    return CompanyService.create_company(db, company_data)


@router.put("/{company_id}", response_model=CompanyResponse)
@limiter.limit(RateLimits.STRICT)
async def update_company(
    request: Request,
    company_id: int,
    company_data: CompanyUpdate,
    db: Session = Depends(get_db)
):
    """
    Update company information.
    
    **Note**: This endpoint is rate-limited more strictly as it modifies data.
    """
    company = CompanyService.update_company(db, company_id, company_data)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return company


@router.delete("/{company_id}", status_code=204)
@limiter.limit(RateLimits.STRICT)
async def delete_company(
    request: Request,
    company_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a company.
    
    **Note**: This endpoint is rate-limited more strictly as it modifies data.
    **Warning**: This will also delete all related financial data.
    """
    success = CompanyService.delete_company(db, company_id)
    if not success:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return None