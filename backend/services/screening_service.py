"""Screening service layer for company filtering and analysis"""

import time
import math
from typing import List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from fastapi import HTTPException

from models.company import Company
from models.financial import FinancialIndicator
from schemas.screening import (
    ScreeningRequest,
    ScreeningFilter,
    ScreeningSort,
    ScreeningResult,
    ComparisonOperator,
    ScreeningSortOrder,
    ScreeningPreset,
    ScreeningFieldInfo
)


class ScreeningService:
    """Service class for company screening functionality"""

    # Mapping of field names to database columns
    FIELD_MAPPING = {
        # Company fields
        "ticker_symbol": Company.ticker_symbol,
        "company_name_jp": Company.company_name_jp,
        "market_division": Company.market_division,
        "industry_code": Company.industry_code,
        "industry_name": Company.industry_name,
        "market_cap": Company.market_cap,
        "shares_outstanding": Company.shares_outstanding,
        "employee_count": Company.employee_count,
        
        # Financial indicator fields
        "roe": FinancialIndicator.roe,
        "roa": FinancialIndicator.roa,
        "operating_margin": FinancialIndicator.operating_margin,
        "net_margin": FinancialIndicator.net_margin,
        "equity_ratio": FinancialIndicator.equity_ratio,
        "debt_to_equity": FinancialIndicator.debt_to_equity,
        "current_ratio": FinancialIndicator.current_ratio,
        "per": FinancialIndicator.per,
        "pbr": FinancialIndicator.pbr,
        "dividend_yield": FinancialIndicator.dividend_yield,
        "revenue_growth": FinancialIndicator.revenue_growth,
        "income_growth": FinancialIndicator.income_growth,
    }

    @staticmethod
    def execute_screening(
        db: Session, 
        request: ScreeningRequest
    ) -> Tuple[List[ScreeningResult], int, float]:
        """Execute company screening with filters and pagination"""
        start_time = time.time()
        
        # Base query with join to financial indicators
        query = (
            db.query(Company, FinancialIndicator)
            .outerjoin(
                FinancialIndicator,
                and_(
                    Company.id == FinancialIndicator.company_id,
                    FinancialIndicator.calculation_date == (
                        db.query(func.max(FinancialIndicator.calculation_date))
                        .filter(FinancialIndicator.company_id == Company.id)
                        .scalar_subquery()
                    )
                )
            )
        )
        
        # Apply filters
        filter_conditions = []
        for filter_item in request.filters:
            condition = ScreeningService._build_filter_condition(filter_item)
            if condition is not None:
                filter_conditions.append(condition)
        
        if filter_conditions:
            query = query.filter(and_(*filter_conditions))
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        if request.sort:
            sort_column = ScreeningService.FIELD_MAPPING.get(request.sort.field)
            if sort_column is not None:
                if request.sort.order == ScreeningSortOrder.DESC:
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
            else:
                # Default sort by market cap descending
                query = query.order_by(desc(Company.market_cap))
        else:
            # Default sort by market cap descending
            query = query.order_by(desc(Company.market_cap))
        
        # Apply pagination
        results = (
            query
            .offset((request.page - 1) * request.size)
            .limit(request.size)
            .all()
        )
        
        # Convert to response format
        screening_results = []
        for company, indicator in results:
            result = ScreeningResult(
                company_id=company.id,
                ticker_symbol=company.ticker_symbol,
                company_name_jp=company.company_name_jp,
                company_name_en=company.company_name_en,
                market_division=company.market_division,
                industry_name=company.industry_name,
                market_cap=company.market_cap
            )
            
            # Add indicators if requested and available
            if request.include_indicators and indicator:
                result.indicators = {
                    "roe": indicator.roe,
                    "roa": indicator.roa,
                    "operating_margin": indicator.operating_margin,
                    "net_margin": indicator.net_margin,
                    "equity_ratio": indicator.equity_ratio,
                    "current_ratio": indicator.current_ratio,
                    "per": indicator.per,
                    "pbr": indicator.pbr,
                    "dividend_yield": indicator.dividend_yield,
                    "revenue_growth": indicator.revenue_growth,
                    "income_growth": indicator.income_growth
                }
            
            screening_results.append(result)
        
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return screening_results, total, execution_time

    @staticmethod
    def _build_filter_condition(filter_item: ScreeningFilter):
        """Build SQLAlchemy filter condition from screening filter"""
        column = ScreeningService.FIELD_MAPPING.get(filter_item.field)
        if column is None:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid filter field: {filter_item.field}"
            )
        
        operator = filter_item.operator
        value = filter_item.value
        
        try:
            if operator == ComparisonOperator.GT:
                return column > value
            elif operator == ComparisonOperator.GTE:
                return column >= value
            elif operator == ComparisonOperator.LT:
                return column < value
            elif operator == ComparisonOperator.LTE:
                return column <= value
            elif operator == ComparisonOperator.EQ:
                return column == value
            elif operator == ComparisonOperator.NEQ:
                return column != value
            elif operator == ComparisonOperator.IN:
                if not isinstance(value, list):
                    raise ValueError("IN operator requires a list value")
                return column.in_(value)
            elif operator == ComparisonOperator.NOT_IN:
                if not isinstance(value, list):
                    raise ValueError("NOT_IN operator requires a list value")
                return ~column.in_(value)
            else:
                raise ValueError(f"Unsupported operator: {operator}")
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filter condition: {str(e)}"
            )

    @staticmethod
    def get_screening_presets() -> List[ScreeningPreset]:
        """Get predefined screening presets"""
        presets = [
            ScreeningPreset(
                id="high_roe",
                name="高ROE企業",
                description="ROE 15%以上の収益性の高い企業",
                category="profitability",
                filters=[
                    ScreeningFilter(
                        field="roe",
                        operator=ComparisonOperator.GTE,
                        value=15.0
                    )
                ],
                sort=ScreeningSort(field="roe", order=ScreeningSortOrder.DESC)
            ),
            ScreeningPreset(
                id="low_per",
                name="低PER割安株",
                description="PER 15倍以下の割安株",
                category="valuation",
                filters=[
                    ScreeningFilter(
                        field="per",
                        operator=ComparisonOperator.LTE,
                        value=15.0
                    ),
                    ScreeningFilter(
                        field="per",
                        operator=ComparisonOperator.GT,
                        value=0
                    )
                ],
                sort=ScreeningSort(field="per", order=ScreeningSortOrder.ASC)
            ),
            ScreeningPreset(
                id="high_dividend",
                name="高配当株",
                description="配当利回り 3%以上の高配当株",
                category="dividend",
                filters=[
                    ScreeningFilter(
                        field="dividend_yield",
                        operator=ComparisonOperator.GTE,
                        value=3.0
                    )
                ],
                sort=ScreeningSort(field="dividend_yield", order=ScreeningSortOrder.DESC)
            ),
            ScreeningPreset(
                id="prime_large_cap",
                name="プライム大型株",
                description="プライム市場の時価総額 1000億円以上",
                category="market",
                filters=[
                    ScreeningFilter(
                        field="market_division",
                        operator=ComparisonOperator.EQ,
                        value="Prime"
                    ),
                    ScreeningFilter(
                        field="market_cap",
                        operator=ComparisonOperator.GTE,
                        value=100000  # 1000億円 (millions)
                    )
                ],
                sort=ScreeningSort(field="market_cap", order=ScreeningSortOrder.DESC)
            ),
            ScreeningPreset(
                id="stable_finance",
                name="財務安定企業",
                description="自己資本比率 50%以上、流動比率 150%以上",
                category="safety",
                filters=[
                    ScreeningFilter(
                        field="equity_ratio",
                        operator=ComparisonOperator.GTE,
                        value=50.0
                    ),
                    ScreeningFilter(
                        field="current_ratio",
                        operator=ComparisonOperator.GTE,
                        value=150.0
                    )
                ],
                sort=ScreeningSort(field="equity_ratio", order=ScreeningSortOrder.DESC)
            ),
            ScreeningPreset(
                id="growth_stocks",
                name="成長株",
                description="売上・利益成長率 20%以上",
                category="growth",
                filters=[
                    ScreeningFilter(
                        field="revenue_growth",
                        operator=ComparisonOperator.GTE,
                        value=20.0
                    ),
                    ScreeningFilter(
                        field="income_growth",
                        operator=ComparisonOperator.GTE,
                        value=20.0
                    )
                ],
                sort=ScreeningSort(field="revenue_growth", order=ScreeningSortOrder.DESC)
            )
        ]
        return presets

    @staticmethod
    def get_available_fields() -> List[ScreeningFieldInfo]:
        """Get information about available screening fields"""
        fields = [
            # Company fields
            ScreeningFieldInfo(
                field="market_cap",
                label="時価総額",
                data_type="number",
                category="company",
                description="時価総額（百万円）",
                min_value=0
            ),
            ScreeningFieldInfo(
                field="market_division",
                label="市場区分",
                data_type="string",
                category="company",
                description="市場区分",
                possible_values=["Prime", "Standard", "Growth"]
            ),
            ScreeningFieldInfo(
                field="industry_name",
                label="業種",
                data_type="string",
                category="company",
                description="業種分類"
            ),
            ScreeningFieldInfo(
                field="employee_count",
                label="従業員数",
                data_type="number",
                category="company",
                description="従業員数（人）",
                min_value=0
            ),
            
            # Financial indicator fields
            ScreeningFieldInfo(
                field="roe",
                label="ROE",
                data_type="number",
                category="profitability",
                description="自己資本利益率（%）",
                min_value=-100,
                max_value=100
            ),
            ScreeningFieldInfo(
                field="roa",
                label="ROA",
                data_type="number",
                category="profitability",
                description="総資産利益率（%）",
                min_value=-100,
                max_value=100
            ),
            ScreeningFieldInfo(
                field="operating_margin",
                label="営業利益率",
                data_type="number",
                category="profitability",
                description="営業利益率（%）",
                min_value=-100,
                max_value=100
            ),
            ScreeningFieldInfo(
                field="equity_ratio",
                label="自己資本比率",
                data_type="number",
                category="safety",
                description="自己資本比率（%）",
                min_value=0,
                max_value=100
            ),
            ScreeningFieldInfo(
                field="current_ratio",
                label="流動比率",
                data_type="number",
                category="safety",
                description="流動比率（%）",
                min_value=0
            ),
            ScreeningFieldInfo(
                field="per",
                label="PER",
                data_type="number",
                category="valuation",
                description="株価収益率（倍）",
                min_value=0
            ),
            ScreeningFieldInfo(
                field="pbr",
                label="PBR",
                data_type="number",
                category="valuation",
                description="株価純資産倍率（倍）",
                min_value=0
            ),
            ScreeningFieldInfo(
                field="dividend_yield",
                label="配当利回り",
                data_type="number",
                category="dividend",
                description="配当利回り（%）",
                min_value=0,
                max_value=20
            ),
            ScreeningFieldInfo(
                field="revenue_growth",
                label="売上成長率",
                data_type="number",
                category="growth",
                description="売上成長率（%）",
                min_value=-100
            ),
            ScreeningFieldInfo(
                field="income_growth",
                label="利益成長率",
                data_type="number",
                category="growth",
                description="当期純利益成長率（%）",
                min_value=-100
            )
        ]
        return fields