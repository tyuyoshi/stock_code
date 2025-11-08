"""Data export API endpoints"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.rate_limiter import limiter, RateLimits
from services.export_service import ExportService
from schemas.export import (
    CompaniesExportRequest,
    ScreeningExportRequest,
    ComparisonExportRequest,
    FinancialDataExportRequest,
    ExportTemplatesResponse,
    ExportFormat,
    ExportDataType,
)

router = APIRouter(
    prefix="/api/v1/export",
    tags=["export"],
    responses={404: {"description": "Not found"}},
)


@router.post("/companies")
@limiter.limit(RateLimits.DATA_EXPORT)
async def export_companies(
    request: Request,
    export_request: CompaniesExportRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Export companies data in various formats.

    **Supported Formats:**
    - CSV: Comma-separated values (UTF-8 with BOM)
    - Excel: Microsoft Excel format (.xlsx)

    **Available Fields:**
    - Basic: ticker_symbol, company_name_jp, company_name_en, market_division, industry_name
    - Financial: market_cap, employee_count, listing_date
    - Indicators: roe, roa, operating_margin, equity_ratio, current_ratio, per, pbr, dividend_yield

    **Example Request:**
    ```json
    {
        "data_type": "companies",
        "format": "excel",
        "company_ids": [1, 2, 3],
        "include_indicators": true,
        "fields": ["ticker_symbol", "company_name_jp", "roe", "per"],
        "filename": "selected_companies"
    }
    ```

    **Note**: This endpoint is rate-limited more strictly due to resource usage.
    """
    try:
        return ExportService.export_companies(db, export_request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/screening")
@limiter.limit(RateLimits.DATA_EXPORT)
async def export_screening_results(
    request: Request,
    export_request: ScreeningExportRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Export screening results.

    Apply the same filters used in screening and export matching companies.

    **Example Request:**
    ```json
    {
        "data_type": "screening_results",
        "format": "csv",
        "filters": [
            {"field": "roe", "operator": "gte", "value": 15.0}
        ],
        "include_indicators": true,
        "max_rows": 500,
        "filename": "high_roe_companies"
    }
    ```

    **Note**: Limited to 10,000 rows per export for performance reasons.
    """
    try:
        return ExportService.export_screening_results(db, export_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/comparison")
@limiter.limit(RateLimits.DATA_EXPORT)
async def export_comparison(
    request: Request,
    export_request: ComparisonExportRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Export company comparison results.

    **Example Request:**
    ```json
    {
        "data_type": "comparison",
        "format": "excel",
        "company_ids": [1, 2, 3, 4],
        "metrics": ["roe", "roa", "per", "pbr"],
        "include_rankings": true,
        "filename": "company_comparison"
    }
    ```

    The exported file will include:
    - Company basic information
    - Selected financial metrics
    - Rankings for each metric (if requested)
    - Summary statistics
    """
    try:
        return ExportService.export_comparison(db, export_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/financial-data")
@limiter.limit(RateLimits.DATA_EXPORT)
async def export_financial_data(
    request: Request,
    export_request: FinancialDataExportRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Export detailed financial data for companies.

    **Available Data Types:**
    - statements: Financial statements (P&L, Balance Sheet, Cash Flow)
    - indicators: Calculated financial indicators
    - stock_prices: Historical stock price data

    **Example Request:**
    ```json
    {
        "data_type": "financial_data",
        "format": "excel",
        "company_ids": [1, 2],
        "data_types": ["statements", "indicators"],
        "periods": 5,
        "filename": "financial_analysis"
    }
    ```

    Multi-sheet Excel files are created with separate sheets for each data type.
    """
    try:
        return ExportService.export_financial_data(db, export_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/templates", response_model=ExportTemplatesResponse)
@limiter.limit(RateLimits.STANDARD)
async def get_export_templates(request: Request):
    """
    Get predefined export templates.

    Returns ready-to-use export configurations:

    **Available Templates:**
    - **基本企業情報**: ティッカー、会社名、市場区分、業種等の基本情報
    - **財務概要**: 基本企業情報 + 主要財務指標
    - **投資分析用データ**: 投資判断に必要な主要指標一覧
    - **スクリーニング結果**: スクリーニング結果のエクスポート用
    - **企業比較レポート**: 複数企業の比較分析レポート

    Use template configurations as starting points for custom exports.
    """
    templates = ExportService.get_export_templates()
    categories = list(set(template.category for template in templates))

    return ExportTemplatesResponse(templates=templates, categories=sorted(categories))


@router.get("/formats")
@limiter.limit(RateLimits.STANDARD)
async def get_supported_formats(request: Request):
    """
    Get information about supported export formats.

    Returns details about available export formats and their capabilities.
    """
    formats = [
        {
            "format": "csv",
            "name": "CSV (Comma-Separated Values)",
            "description": "Plain text format, widely supported",
            "file_extension": ".csv",
            "media_type": "text/csv",
            "supports_multiple_sheets": False,
            "max_file_size_mb": 100,
            "best_for": [
                "Simple data export",
                "Import to other systems",
                "Large datasets",
            ],
        },
        {
            "format": "excel",
            "name": "Microsoft Excel",
            "description": "Excel workbook format with formatting support",
            "file_extension": ".xlsx",
            "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "supports_multiple_sheets": True,
            "max_file_size_mb": 50,
            "best_for": [
                "Business reports",
                "Data analysis",
                "Formatted presentations",
            ],
        },
        {
            "format": "pdf",
            "name": "PDF Report",
            "description": "Formatted report document (planned)",
            "file_extension": ".pdf",
            "media_type": "application/pdf",
            "supports_multiple_sheets": False,
            "max_file_size_mb": 25,
            "best_for": ["Presentation reports", "Print-ready documents"],
            "status": "planned",
        },
    ]

    return {"formats": formats}
