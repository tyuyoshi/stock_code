"""Export service layer for data export functionality"""

import io
import csv
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, BinaryIO
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from models.company import Company
from models.financial import FinancialStatement, FinancialIndicator
from schemas.export import (
    ExportFormat,
    ExportDataType,
    CompaniesExportRequest,
    ScreeningExportRequest,
    ComparisonExportRequest,
    FinancialDataExportRequest,
    ExportTemplate
)
from services.company_service import CompanyService
from services.screening_service import ScreeningService
from services.compare_service import CompareService


class ExportService:
    """Service class for data export functionality"""

    @staticmethod
    def export_companies(
        db: Session,
        request: CompaniesExportRequest
    ) -> StreamingResponse:
        """Export companies data"""
        
        # Get companies data
        if request.company_ids:
            companies = (
                db.query(Company)
                .filter(Company.id.in_(request.company_ids))
                .all()
            )
        else:
            companies = db.query(Company).all()
        
        # Get financial indicators if requested
        indicators_map = {}
        if request.include_indicators:
            for company in companies:
                indicator = (
                    db.query(FinancialIndicator)
                    .filter(FinancialIndicator.company_id == company.id)
                    .order_by(FinancialIndicator.calculation_date.desc())
                    .first()
                )
                indicators_map[company.id] = indicator

        # Determine fields to include
        if request.fields:
            fields = request.fields
        else:
            fields = ExportService._get_default_company_fields(request.include_indicators)

        # Generate export data
        if request.format == ExportFormat.CSV:
            return ExportService._export_companies_csv(
                companies, indicators_map, fields, request
            )
        elif request.format == ExportFormat.EXCEL:
            return ExportService._export_companies_excel(
                companies, indicators_map, fields, request
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")

    @staticmethod
    def _export_companies_csv(
        companies: List[Company],
        indicators_map: Dict[int, FinancialIndicator],
        fields: List[str],
        request: CompaniesExportRequest
    ) -> StreamingResponse:
        """Export companies data as CSV"""
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        if request.include_headers:
            headers = ExportService._get_field_labels(fields)
            writer.writerow(headers)
        
        # Write data rows
        for company in companies:
            row = []
            indicator = indicators_map.get(company.id)
            
            for field in fields:
                value = ExportService._get_field_value(company, indicator, field)
                row.append(value)
            
            writer.writerow(row)
        
        output.seek(0)
        
        filename = request.filename or f"companies_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
        )

    @staticmethod
    def _export_companies_excel(
        companies: List[Company],
        indicators_map: Dict[int, FinancialIndicator],
        fields: List[str],
        request: CompaniesExportRequest
    ) -> StreamingResponse:
        """Export companies data as Excel"""
        
        try:
            import openpyxl
            from openpyxl.utils import get_column_letter
        except ImportError:
            raise HTTPException(
                status_code=500, 
                detail="Excel export requires openpyxl package"
            )
        
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "Companies"
        
        # Write headers
        if request.include_headers:
            headers = ExportService._get_field_labels(fields)
            for col, header in enumerate(headers, 1):
                worksheet.cell(row=1, column=col, value=header)
        
        # Write data rows
        start_row = 2 if request.include_headers else 1
        for row_idx, company in enumerate(companies, start_row):
            indicator = indicators_map.get(company.id)
            
            for col_idx, field in enumerate(fields, 1):
                value = ExportService._get_field_value(company, indicator, field)
                worksheet.cell(row=row_idx, column=col_idx, value=value)
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Save to BytesIO
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        
        filename = request.filename or f"companies_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )

    @staticmethod
    def _get_default_company_fields(include_indicators: bool) -> List[str]:
        """Get default fields for company export"""
        fields = [
            "ticker_symbol", "company_name_jp", "company_name_en",
            "market_division", "industry_name", "market_cap",
            "employee_count", "listing_date"
        ]
        
        if include_indicators:
            fields.extend([
                "roe", "roa", "operating_margin", "equity_ratio",
                "current_ratio", "per", "pbr", "dividend_yield"
            ])
        
        return fields

    @staticmethod
    def _get_field_labels(fields: List[str]) -> List[str]:
        """Get human-readable labels for fields"""
        label_map = {
            "ticker_symbol": "ティッカー",
            "company_name_jp": "会社名",
            "company_name_en": "会社名（英語）",
            "market_division": "市場区分",
            "industry_name": "業種",
            "market_cap": "時価総額（百万円）",
            "employee_count": "従業員数",
            "listing_date": "上場日",
            "roe": "ROE（%）",
            "roa": "ROA（%）",
            "operating_margin": "営業利益率（%）",
            "equity_ratio": "自己資本比率（%）",
            "current_ratio": "流動比率（%）",
            "per": "PER（倍）",
            "pbr": "PBR（倍）",
            "dividend_yield": "配当利回り（%）"
        }
        
        return [label_map.get(field, field) for field in fields]

    @staticmethod
    def _get_field_value(
        company: Company, 
        indicator: Optional[FinancialIndicator], 
        field: str
    ) -> Any:
        """Get field value from company or indicator"""
        
        # Company fields
        if hasattr(company, field):
            value = getattr(company, field)
            if field == "listing_date" and value:
                return value.strftime("%Y-%m-%d")
            return value
        
        # Indicator fields
        if indicator and hasattr(indicator, field):
            return getattr(indicator, field)
        
        return None

    @staticmethod
    def get_export_templates() -> List[ExportTemplate]:
        """Get predefined export templates"""
        templates = [
            ExportTemplate(
                id="basic_companies",
                name="基本企業情報",
                description="ティッカー、会社名、市場区分、業種等の基本情報",
                data_type=ExportDataType.COMPANIES,
                format=ExportFormat.CSV,
                fields=["ticker_symbol", "company_name_jp", "market_division", "industry_name"],
                category="basic"
            ),
            ExportTemplate(
                id="financial_overview",
                name="財務概要",
                description="基本企業情報 + 主要財務指標",
                data_type=ExportDataType.COMPANIES,
                format=ExportFormat.EXCEL,
                fields=[
                    "ticker_symbol", "company_name_jp", "market_division", "market_cap",
                    "roe", "roa", "operating_margin", "equity_ratio", "per", "pbr"
                ],
                category="financial"
            ),
            ExportTemplate(
                id="investment_analysis",
                name="投資分析用データ",
                description="投資判断に必要な主要指標一覧",
                data_type=ExportDataType.COMPANIES,
                format=ExportFormat.EXCEL,
                fields=[
                    "ticker_symbol", "company_name_jp", "market_cap", "per", "pbr",
                    "dividend_yield", "roe", "equity_ratio", "revenue_growth", "income_growth"
                ],
                category="investment"
            ),
            ExportTemplate(
                id="screening_results",
                name="スクリーニング結果",
                description="スクリーニング結果のエクスポート用テンプレート",
                data_type=ExportDataType.SCREENING_RESULTS,
                format=ExportFormat.CSV,
                fields=[
                    "ticker_symbol", "company_name_jp", "market_division", 
                    "roe", "per", "dividend_yield"
                ],
                category="screening"
            ),
            ExportTemplate(
                id="comparison_report",
                name="企業比較レポート",
                description="複数企業の比較分析レポート",
                data_type=ExportDataType.COMPARISON,
                format=ExportFormat.EXCEL,
                fields=[
                    "ticker_symbol", "company_name_jp", "roe", "roa", "per", "pbr",
                    "equity_ratio", "current_ratio"
                ],
                category="comparison"
            )
        ]
        return templates