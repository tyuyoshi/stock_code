"""Screening API endpoints"""

import math
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.rate_limiter import limiter, RateLimits
from services.screening_service import ScreeningService
from schemas.screening import (
    ScreeningRequest,
    ScreeningResponse,
    ScreeningPresetsResponse,
    ScreeningFieldsResponse
)

router = APIRouter(
    prefix="/api/v1/screening",
    tags=["screening"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=ScreeningResponse)
@limiter.limit(RateLimits.STANDARD)
async def execute_screening(
    request: Request,
    screening_request: ScreeningRequest,
    db: Session = Depends(get_db)
):
    """
    Execute company screening with custom filters.
    
    Apply multiple filters to find companies matching specific criteria:
    
    **Available Filter Fields:**
    - Company: market_cap, market_division, industry_name, employee_count
    - Profitability: roe, roa, operating_margin, net_margin
    - Safety: equity_ratio, current_ratio, debt_to_equity
    - Valuation: per, pbr, dividend_yield
    - Growth: revenue_growth, income_growth
    
    **Filter Operators:**
    - gt, gte: Greater than (or equal)
    - lt, lte: Less than (or equal)
    - eq, neq: Equal (or not equal)
    - in, not_in: In list (or not in list)
    
    **Example Request:**
    ```json
    {
        "filters": [
            {"field": "roe", "operator": "gte", "value": 15.0},
            {"field": "market_division", "operator": "eq", "value": "Prime"}
        ],
        "sort": {"field": "roe", "order": "desc"},
        "page": 1,
        "size": 20,
        "include_indicators": true
    }
    ```
    """
    try:
        results, total, execution_time = ScreeningService.execute_screening(
            db, screening_request
        )
        
        total_pages = math.ceil(total / screening_request.size) if total > 0 else 0
        
        return ScreeningResponse(
            results=results,
            total=total,
            page=screening_request.page,
            size=screening_request.size,
            total_pages=total_pages,
            applied_filters=screening_request.filters,
            execution_time_ms=execution_time
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/presets", response_model=ScreeningPresetsResponse)
@limiter.limit(RateLimits.STANDARD)
async def get_screening_presets(request: Request):
    """
    Get predefined screening presets.
    
    Returns popular screening configurations:
    - **High ROE**: ROE 15%以上の収益性の高い企業
    - **Low PER**: PER 15倍以下の割安株
    - **High Dividend**: 配当利回り 3%以上の高配当株
    - **Prime Large Cap**: プライム市場の大型株
    - **Stable Finance**: 財務安定企業
    - **Growth Stocks**: 高成長株
    
    Use these presets as starting points or apply them directly.
    """
    presets = ScreeningService.get_screening_presets()
    categories = list(set(preset.category for preset in presets))
    
    return ScreeningPresetsResponse(
        presets=presets,
        categories=sorted(categories)
    )


@router.get("/presets/{preset_id}", response_model=ScreeningResponse)
@limiter.limit(RateLimits.STANDARD)
async def execute_preset_screening(
    request: Request,
    preset_id: str,
    page: int = 1,
    size: int = 20,
    include_indicators: bool = True,
    db: Session = Depends(get_db)
):
    """
    Execute screening using a predefined preset.
    
    Apply a predefined screening configuration by preset ID.
    """
    presets = ScreeningService.get_screening_presets()
    preset = next((p for p in presets if p.id == preset_id), None)
    
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    screening_request = ScreeningRequest(
        filters=preset.filters,
        sort=preset.sort,
        page=page,
        size=size,
        include_indicators=include_indicators
    )
    
    try:
        results, total, execution_time = ScreeningService.execute_screening(
            db, screening_request
        )
        
        total_pages = math.ceil(total / size) if total > 0 else 0
        
        return ScreeningResponse(
            results=results,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
            applied_filters=preset.filters,
            execution_time_ms=execution_time
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fields", response_model=ScreeningFieldsResponse)
@limiter.limit(RateLimits.STANDARD)
async def get_screening_fields(request: Request):
    """
    Get information about available screening fields.
    
    Returns metadata about all fields that can be used for screening:
    - Field names and labels
    - Data types and value ranges
    - Field categories and descriptions
    
    Use this endpoint to build dynamic screening UIs.
    """
    fields = ScreeningService.get_available_fields()
    categories = list(set(field.category for field in fields))
    
    return ScreeningFieldsResponse(
        fields=fields,
        categories=sorted(categories)
    )