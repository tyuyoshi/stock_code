"""Screening-related Pydantic schemas for API requests and responses"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class ComparisonOperator(str, Enum):
    """Comparison operators for screening filters"""
    GT = "gt"  # greater than
    GTE = "gte"  # greater than or equal
    LT = "lt"  # less than
    LTE = "lte"  # less than or equal
    EQ = "eq"  # equal
    NEQ = "neq"  # not equal
    IN = "in"  # in list
    NOT_IN = "not_in"  # not in list


class ScreeningFilter(BaseModel):
    """Individual screening filter"""
    field: str = Field(..., description="Field name to filter on")
    operator: ComparisonOperator = Field(..., description="Comparison operator")
    value: Union[float, int, str, List[Union[float, int, str]]] = Field(
        ..., description="Value to compare against"
    )


class ScreeningSortOrder(str, Enum):
    """Sort order for screening results"""
    ASC = "asc"
    DESC = "desc"


class ScreeningSort(BaseModel):
    """Sorting configuration for screening"""
    field: str = Field(..., description="Field name to sort by")
    order: ScreeningSortOrder = Field(default=ScreeningSortOrder.DESC, description="Sort order")


class ScreeningRequest(BaseModel):
    """Request schema for company screening"""
    filters: List[ScreeningFilter] = Field(
        default_factory=list, 
        description="List of filters to apply"
    )
    sort: Optional[ScreeningSort] = Field(
        None, 
        description="Sorting configuration"
    )
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    include_indicators: bool = Field(
        True, 
        description="Include financial indicators in response"
    )


class ScreeningResult(BaseModel):
    """Individual company result from screening"""
    company_id: int
    ticker_symbol: str
    company_name_jp: str
    company_name_en: Optional[str] = None
    market_division: Optional[str] = None
    industry_name: Optional[str] = None
    market_cap: Optional[float] = None
    indicators: Optional[Dict[str, Any]] = Field(
        None, 
        description="Financial indicators if requested"
    )

    class Config:
        from_attributes = True


class ScreeningResponse(BaseModel):
    """Response schema for screening results"""
    results: List[ScreeningResult]
    total: int = Field(..., description="Total number of companies matching criteria")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    applied_filters: List[ScreeningFilter] = Field(
        ..., 
        description="Filters that were applied"
    )
    execution_time_ms: Optional[float] = Field(
        None, 
        description="Query execution time in milliseconds"
    )


class ScreeningPreset(BaseModel):
    """Predefined screening preset"""
    id: str = Field(..., description="Preset identifier")
    name: str = Field(..., description="Human-readable preset name")
    description: str = Field(..., description="Preset description")
    filters: List[ScreeningFilter] = Field(..., description="Preset filters")
    sort: Optional[ScreeningSort] = None
    category: str = Field(..., description="Preset category")


class ScreeningPresetsResponse(BaseModel):
    """Response schema for screening presets"""
    presets: List[ScreeningPreset]
    categories: List[str] = Field(..., description="Available preset categories")


class SavedScreeningFilter(BaseModel):
    """Saved screening configuration"""
    name: str = Field(..., min_length=1, max_length=100, description="Filter name")
    description: Optional[str] = Field(None, max_length=500, description="Filter description")
    filters: List[ScreeningFilter] = Field(..., description="Screening filters")
    sort: Optional[ScreeningSort] = None
    is_public: bool = Field(False, description="Whether filter is public")


class SavedScreeningResponse(BaseModel):
    """Response schema for saved screening filters"""
    id: int
    name: str
    description: Optional[str]
    filters: List[ScreeningFilter]
    sort: Optional[ScreeningSort]
    is_public: bool
    created_at: str
    updated_at: Optional[str]
    user_id: Optional[int] = None  # For future user system

    class Config:
        from_attributes = True


class ScreeningFieldInfo(BaseModel):
    """Information about available screening fields"""
    field: str = Field(..., description="Field name")
    label: str = Field(..., description="Human-readable label")
    data_type: str = Field(..., description="Data type (number, string, date)")
    category: str = Field(..., description="Field category")
    description: str = Field(..., description="Field description")
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    possible_values: Optional[List[str]] = None  # For enum-like fields


class ScreeningFieldsResponse(BaseModel):
    """Response schema for available screening fields"""
    fields: List[ScreeningFieldInfo]
    categories: List[str] = Field(..., description="Available field categories")