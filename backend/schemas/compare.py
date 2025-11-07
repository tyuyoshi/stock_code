"""Company comparison-related Pydantic schemas for API requests and responses"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    """Request schema for company comparison"""
    company_ids: List[int] = Field(
        ..., 
        min_items=2, 
        max_items=10, 
        description="List of company IDs to compare (2-10 companies)"
    )
    metrics: Optional[List[str]] = Field(
        None,
        description="Specific metrics to include in comparison. If not provided, all available metrics are included"
    )
    include_rankings: bool = Field(
        True,
        description="Include ranking information for each metric"
    )


class CompanyComparisonData(BaseModel):
    """Individual company data in comparison"""
    company_id: int
    ticker_symbol: str
    company_name_jp: str
    company_name_en: Optional[str] = None
    market_division: Optional[str] = None
    industry_name: Optional[str] = None
    
    # Basic company info
    market_cap: Optional[float] = None
    employee_count: Optional[int] = None
    
    # Financial indicators
    profitability: Dict[str, Optional[float]] = Field(default_factory=dict)
    safety: Dict[str, Optional[float]] = Field(default_factory=dict)
    efficiency: Dict[str, Optional[float]] = Field(default_factory=dict)
    growth: Dict[str, Optional[float]] = Field(default_factory=dict)
    valuation: Dict[str, Optional[float]] = Field(default_factory=dict)
    cash_flow: Dict[str, Optional[float]] = Field(default_factory=dict)
    
    # Rankings (if requested)
    rankings: Optional[Dict[str, int]] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class ComparisonSummary(BaseModel):
    """Summary statistics for the comparison"""
    total_companies: int
    metrics_compared: List[str]
    best_performers: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Best performing company for each metric"
    )
    worst_performers: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Worst performing company for each metric"
    )
    averages: Dict[str, Optional[float]] = Field(
        default_factory=dict,
        description="Average values for each metric"
    )


class CompareResponse(BaseModel):
    """Response schema for company comparison"""
    companies: List[CompanyComparisonData]
    summary: ComparisonSummary
    comparison_date: str = Field(..., description="Date when comparison was generated")
    requested_metrics: Optional[List[str]] = None


class ComparisonTemplate(BaseModel):
    """Predefined comparison template"""
    id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    metrics: List[str] = Field(..., description="Metrics included in template")
    category: str = Field(..., description="Template category")


class ComparisonTemplatesResponse(BaseModel):
    """Response schema for comparison templates"""
    templates: List[ComparisonTemplate]
    categories: List[str] = Field(..., description="Available template categories")


class MetricInfo(BaseModel):
    """Information about a comparison metric"""
    metric: str = Field(..., description="Metric identifier")
    label: str = Field(..., description="Human-readable label")
    category: str = Field(..., description="Metric category")
    unit: str = Field(..., description="Unit of measurement")
    description: str = Field(..., description="Metric description")
    higher_is_better: bool = Field(..., description="Whether higher values are better")


class ComparisonMetricsResponse(BaseModel):
    """Response schema for available comparison metrics"""
    metrics: List[MetricInfo]
    categories: List[str] = Field(..., description="Available metric categories")