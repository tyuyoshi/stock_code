"""Company comparison API endpoints"""

import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from core.database import get_db
from core.rate_limiter import limiter, RateLimits
from services.compare_service import CompareService
from schemas.compare import (
    CompareRequest,
    CompareResponse,
    ComparisonTemplatesResponse,
    ComparisonMetricsResponse
)

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/compare",
    tags=["compare"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=CompareResponse)
@limiter.limit(RateLimits.STANDARD)
async def compare_companies(
    request: Request,
    compare_request: CompareRequest,
    db: Session = Depends(get_db)
):
    """
    Compare multiple companies across financial metrics.
    
    Analyze and compare 2-10 companies side by side:
    
    **Features:**
    - Side-by-side comparison of financial indicators
    - Automatic ranking for each metric
    - Best/worst performer identification
    - Average calculations across compared companies
    
    **Available Metrics Categories:**
    - **Profitability**: ROE, ROA, operating margin, net margin
    - **Safety**: Equity ratio, debt ratios, liquidity ratios
    - **Efficiency**: Asset turnover, inventory turnover
    - **Growth**: Revenue growth, income growth, asset growth
    - **Valuation**: P/E, P/B, dividend yield, EV/EBITDA
    - **Cash Flow**: Operating CF margin, free cash flow ratios
    
    **Example Request:**
    ```json
    {
        "company_ids": [1, 2, 3],
        "metrics": ["roe", "roa", "per", "pbr"],
        "include_rankings": true
    }
    ```
    
    If `metrics` is not specified, all available metrics are included.
    """
    try:
        companies, summary = CompareService.compare_companies(db, compare_request)
        
        return CompareResponse(
            companies=companies,
            summary=summary,
            comparison_date=datetime.now().isoformat(),
            requested_metrics=compare_request.metrics
        )
    except ValueError as e:
        logger.warning(f"Invalid comparison request: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid comparison: {str(e)}")
    except SQLAlchemyError as e:
        logger.error(f"Database error in comparison: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.error(f"Unexpected error in comparison: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/templates", response_model=ComparisonTemplatesResponse)
@limiter.limit(RateLimits.STANDARD)
async def get_comparison_templates(request: Request):
    """
    Get predefined comparison templates.
    
    Returns ready-to-use comparison configurations:
    
    **Available Templates:**
    - **収益性分析**: ROE、ROA、各種利益率による収益性比較
    - **財務安全性分析**: 自己資本比率、流動比率等による財務安全性比較
    - **株価指標比較**: PER、PBR、配当利回り等による投資指標比較
    - **成長性分析**: 売上・利益成長率による成長性比較
    - **効率性分析**: 資産回転率等による経営効率性比較
    - **総合分析**: 主要指標による総合的な企業比較
    
    Use template IDs with `/compare/templates/{template_id}` endpoint.
    """
    templates = CompareService.get_comparison_templates()
    categories = list(set(template.category for template in templates))
    
    return ComparisonTemplatesResponse(
        templates=templates,
        categories=sorted(categories)
    )


@router.post("/templates/{template_id}", response_model=CompareResponse)
@limiter.limit(RateLimits.STANDARD)
async def compare_using_template(
    request: Request,
    template_id: str,
    company_ids: List[int],
    include_rankings: bool = True,
    db: Session = Depends(get_db)
):
    """
    Compare companies using a predefined template.
    
    Apply a predefined comparison template to the specified companies.
    
    **Request Body:**
    ```json
    {
        "company_ids": [1, 2, 3, 4],
        "include_rankings": true
    }
    ```
    """
    templates = CompareService.get_comparison_templates()
    template = next((t for t in templates if t.id == template_id), None)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    compare_request = CompareRequest(
        company_ids=company_ids,
        metrics=template.metrics,
        include_rankings=include_rankings
    )
    
    try:
        companies, summary = CompareService.compare_companies(db, compare_request)
        
        return CompareResponse(
            companies=companies,
            summary=summary,
            comparison_date=datetime.now().isoformat(),
            requested_metrics=template.metrics
        )
    except ValueError as e:
        logger.warning(f"Invalid template comparison request: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid comparison: {str(e)}")
    except SQLAlchemyError as e:
        logger.error(f"Database error in template comparison: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.error(f"Unexpected error in template comparison: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/metrics", response_model=ComparisonMetricsResponse)
@limiter.limit(RateLimits.STANDARD)
async def get_comparison_metrics(request: Request):
    """
    Get information about available comparison metrics.
    
    Returns detailed information about all metrics that can be used for comparison:
    - Metric names and labels
    - Categories and units
    - Descriptions and interpretation guidance
    - Whether higher values are better for each metric
    
    Use this endpoint to build dynamic comparison UIs.
    """
    metrics = CompareService.get_available_metrics()
    categories = list(set(metric.category for metric in metrics))
    
    return ComparisonMetricsResponse(
        metrics=metrics,
        categories=sorted(categories)
    )