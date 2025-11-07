"""Export-related Pydantic schemas for API requests and responses"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ExportFormat(str, Enum):
    """Supported export formats"""
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"


class ExportDataType(str, Enum):
    """Types of data that can be exported"""
    COMPANIES = "companies"
    SCREENING_RESULTS = "screening_results"
    COMPARISON = "comparison"
    FINANCIAL_DATA = "financial_data"


class ExportRequest(BaseModel):
    """Base request schema for data export"""
    data_type: ExportDataType = Field(..., description="Type of data to export")
    format: ExportFormat = Field(..., description="Export format")
    filename: Optional[str] = Field(None, max_length=100, description="Custom filename (without extension)")
    include_headers: bool = Field(True, description="Include column headers")
    

class CompaniesExportRequest(ExportRequest):
    """Request schema for companies list export"""
    company_ids: Optional[List[int]] = Field(None, description="Specific company IDs to export. If not provided, exports all companies")
    include_indicators: bool = Field(True, description="Include financial indicators")
    fields: Optional[List[str]] = Field(None, description="Specific fields to include")


class ScreeningExportRequest(ExportRequest):
    """Request schema for screening results export"""
    filters: List[Dict[str, Any]] = Field(..., description="Screening filters used")
    sort: Optional[Dict[str, str]] = None
    include_indicators: bool = Field(True, description="Include financial indicators")
    max_rows: int = Field(1000, ge=1, le=10000, description="Maximum number of rows to export")


class ComparisonExportRequest(ExportRequest):
    """Request schema for comparison results export"""
    company_ids: List[int] = Field(..., min_items=2, max_items=10, description="Company IDs to compare")
    metrics: Optional[List[str]] = Field(None, description="Specific metrics to include")
    include_rankings: bool = Field(True, description="Include ranking information")


class FinancialDataExportRequest(ExportRequest):
    """Request schema for financial data export"""
    company_ids: List[int] = Field(..., min_items=1, description="Company IDs")
    data_types: List[str] = Field(
        default=["statements", "indicators"], 
        description="Types of financial data to include"
    )
    periods: int = Field(5, ge=1, le=20, description="Number of periods to include")


class ExportResponse(BaseModel):
    """Response schema for export operations"""
    export_id: str = Field(..., description="Unique export identifier")
    filename: str = Field(..., description="Generated filename")
    format: ExportFormat = Field(..., description="Export format")
    data_type: ExportDataType = Field(..., description="Data type exported")
    status: str = Field(..., description="Export status")
    download_url: str = Field(..., description="URL to download the exported file")
    created_at: str = Field(..., description="Export creation timestamp")
    expires_at: str = Field(..., description="Download URL expiration timestamp")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    row_count: Optional[int] = Field(None, description="Number of rows exported")


class ExportTemplate(BaseModel):
    """Predefined export template"""
    id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    data_type: ExportDataType = Field(..., description="Data type")
    format: ExportFormat = Field(..., description="Export format")
    fields: List[str] = Field(..., description="Fields included in template")
    category: str = Field(..., description="Template category")


class ExportTemplatesResponse(BaseModel):
    """Response schema for export templates"""
    templates: List[ExportTemplate]
    categories: List[str] = Field(..., description="Available template categories")


class ExportHistoryItem(BaseModel):
    """Individual export history item"""
    export_id: str
    filename: str
    format: ExportFormat
    data_type: ExportDataType
    status: str
    created_at: str
    expires_at: str
    file_size_bytes: Optional[int] = None
    row_count: Optional[int] = None
    download_count: int = Field(0, description="Number of times downloaded")


class ExportHistoryResponse(BaseModel):
    """Response schema for export history"""
    exports: List[ExportHistoryItem]
    total: int = Field(..., description="Total number of exports")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")