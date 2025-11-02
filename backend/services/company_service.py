"""Company service layer for business logic"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException

from models.company import Company
from models.financial import FinancialStatement, FinancialIndicator
from schemas.company import (
    CompanyCreate, 
    CompanyUpdate, 
    CompanySearchParams,
    FinancialDataResponse,
    FinancialIndicatorsResponse
)


def sanitize_search_term(term: str) -> str:
    """
    Sanitize search term for SQL LIKE operations.
    Escapes SQL wildcard characters (%, _) to prevent unintended pattern matching.
    """
    return term.replace('%', '\\%').replace('_', '\\_')


class CompanyService:
    """Service class for company-related business logic"""

    @staticmethod
    def get_company_by_id(db: Session, company_id: int) -> Optional[Company]:
        """Get company by ID"""
        return db.query(Company).filter(Company.id == company_id).first()

    @staticmethod
    def get_company_by_ticker(db: Session, ticker_symbol: str) -> Optional[Company]:
        """Get company by ticker symbol"""
        return db.query(Company).filter(Company.ticker_symbol == ticker_symbol).first()

    @staticmethod
    def get_companies(
        db: Session, 
        search_params: CompanySearchParams
    ) -> Tuple[List[Company], int]:
        """Get companies with search and pagination"""
        query = db.query(Company)
        
        # Apply search filters
        if search_params.q:
            sanitized_term = sanitize_search_term(search_params.q)
            search_term = f"%{sanitized_term}%"
            query = query.filter(
                or_(
                    Company.company_name_jp.ilike(search_term),
                    Company.company_name_en.ilike(search_term),
                    Company.ticker_symbol.ilike(search_term)
                )
            )
        
        if search_params.market_division:
            query = query.filter(Company.market_division == search_params.market_division)
            
        if search_params.industry_code:
            query = query.filter(Company.industry_code == search_params.industry_code)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        companies = (
            query
            .order_by(Company.market_cap.desc().nulls_last(), Company.ticker_symbol)
            .offset((search_params.page - 1) * search_params.size)
            .limit(search_params.size)
            .all()
        )
        
        return companies, total

    @staticmethod
    def create_company(db: Session, company_data: CompanyCreate) -> Company:
        """Create new company"""
        # Check if ticker already exists
        existing = CompanyService.get_company_by_ticker(db, company_data.ticker_symbol)
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Company with ticker {company_data.ticker_symbol} already exists"
            )
        
        db_company = Company(**company_data.model_dump())
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
        return db_company

    @staticmethod
    def update_company(
        db: Session, 
        company_id: int, 
        company_data: CompanyUpdate
    ) -> Optional[Company]:
        """Update company data"""
        db_company = CompanyService.get_company_by_id(db, company_id)
        if not db_company:
            return None
        
        update_data = company_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_company, field, value)
        
        db.commit()
        db.refresh(db_company)
        return db_company

    @staticmethod
    def delete_company(db: Session, company_id: int) -> bool:
        """Delete company"""
        db_company = CompanyService.get_company_by_id(db, company_id)
        if not db_company:
            return False
        
        db.delete(db_company)
        db.commit()
        return True

    @staticmethod
    def get_company_financials(
        db: Session, 
        company_id: int,
        limit: int = 5
    ) -> FinancialDataResponse:
        """Get company's financial statements"""
        company = CompanyService.get_company_by_id(db, company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get latest financial statements
        statements = (
            db.query(FinancialStatement)
            .filter(FinancialStatement.company_id == company_id)
            .order_by(desc(FinancialStatement.period_end_date))
            .limit(limit)
            .all()
        )
        
        # Convert to dict format
        financial_data = []
        latest_period = None
        
        for stmt in statements:
            if not latest_period:
                latest_period = stmt.period_end_date.strftime("%Y-%m-%d") if stmt.period_end_date else None
            
            financial_data.append({
                "period_end_date": stmt.period_end_date.isoformat() if stmt.period_end_date else None,
                "statement_type": stmt.statement_type,
                "revenue": stmt.revenue,
                "operating_income": stmt.operating_income,
                "net_income": stmt.net_income,
                "total_assets": stmt.total_assets,
                "total_equity": stmt.total_equity,
                "total_liabilities": stmt.total_liabilities,
                "operating_cash_flow": stmt.operating_cash_flow,
                "investing_cash_flow": stmt.investing_cash_flow,
                "financing_cash_flow": stmt.financing_cash_flow
            })
        
        return FinancialDataResponse(
            company_id=company_id,
            financial_statements=financial_data,
            latest_period=latest_period
        )

    @staticmethod
    def get_company_indicators(
        db: Session, 
        company_id: int
    ) -> FinancialIndicatorsResponse:
        """Get company's financial indicators"""
        company = CompanyService.get_company_by_id(db, company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get latest financial indicators
        indicator = (
            db.query(FinancialIndicator)
            .filter(FinancialIndicator.company_id == company_id)
            .order_by(desc(FinancialIndicator.calculation_date))
            .first()
        )
        
        if not indicator:
            return FinancialIndicatorsResponse(
                company_id=company_id,
                indicators={},
                calculation_date=None,
                period=None
            )
        
        # Organize indicators by category
        indicators_dict = {
            "profitability": {
                "roe": indicator.roe,
                "roa": indicator.roa,
                "operating_margin": indicator.operating_margin,
                "net_margin": indicator.net_margin,
                "gross_margin": indicator.gross_margin
            },
            "safety": {
                "equity_ratio": indicator.equity_ratio,
                "debt_to_equity": indicator.debt_to_equity,
                "current_ratio": indicator.current_ratio,
                "quick_ratio": indicator.quick_ratio,
                "interest_coverage": indicator.interest_coverage
            },
            "efficiency": {
                "asset_turnover": indicator.asset_turnover,
                "inventory_turnover": indicator.inventory_turnover,
                "receivables_turnover": indicator.receivables_turnover,
                "working_capital_turnover": indicator.working_capital_turnover
            },
            "growth": {
                "revenue_growth": indicator.revenue_growth,
                "income_growth": indicator.income_growth,
                "asset_growth": indicator.asset_growth,
                "equity_growth": indicator.equity_growth
            },
            "valuation": {
                "per": indicator.per,
                "pbr": indicator.pbr,
                "pcfr": indicator.pcfr,
                "ev_ebitda": indicator.ev_ebitda,
                "dividend_yield": indicator.dividend_yield
            },
            "cash_flow": {
                "operating_cf_margin": indicator.operating_cf_margin,
                "free_cash_flow": indicator.free_cash_flow,
                "cf_to_debt": indicator.cf_to_debt,
                "capex_ratio": indicator.capex_ratio
            }
        }
        
        return FinancialIndicatorsResponse(
            company_id=company_id,
            indicators=indicators_dict,
            calculation_date=indicator.calculation_date,
            period=indicator.period
        )