"""Company comparison service layer"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException

from models.company import Company
from models.financial import FinancialIndicator
from schemas.compare import (
    CompareRequest,
    CompanyComparisonData,
    ComparisonSummary,
    ComparisonTemplate,
    MetricInfo
)


class CompareService:
    """Service class for company comparison functionality"""

    # Available metrics for comparison
    AVAILABLE_METRICS = {
        "profitability": ["roe", "roa", "operating_margin", "net_margin", "gross_margin"],
        "safety": ["equity_ratio", "debt_to_equity", "current_ratio", "quick_ratio", "interest_coverage"],
        "efficiency": ["asset_turnover", "inventory_turnover", "receivables_turnover", "working_capital_turnover"],
        "growth": ["revenue_growth", "income_growth", "asset_growth", "equity_growth"],
        "valuation": ["per", "pbr", "pcfr", "ev_ebitda", "dividend_yield"],
        "cash_flow": ["operating_cf_margin", "free_cash_flow", "cf_to_debt", "capex_ratio"]
    }

    # Metrics where higher values are better
    HIGHER_IS_BETTER = {
        "roe", "roa", "operating_margin", "net_margin", "gross_margin",
        "equity_ratio", "current_ratio", "quick_ratio", "interest_coverage",
        "asset_turnover", "inventory_turnover", "receivables_turnover", "working_capital_turnover",
        "revenue_growth", "income_growth", "asset_growth", "equity_growth",
        "dividend_yield", "operating_cf_margin", "free_cash_flow", "cf_to_debt"
    }

    @staticmethod
    def compare_companies(
        db: Session,
        request: CompareRequest
    ) -> tuple[List[CompanyComparisonData], ComparisonSummary]:
        """Compare multiple companies across financial metrics"""
        
        # Validate company IDs
        companies = (
            db.query(Company)
            .filter(Company.id.in_(request.company_ids))
            .all()
        )
        
        if len(companies) != len(request.company_ids):
            found_ids = {c.id for c in companies}
            missing_ids = set(request.company_ids) - found_ids
            raise HTTPException(
                status_code=404,
                detail=f"Companies not found: {list(missing_ids)}"
            )

        # Get latest financial indicators for each company
        indicators = {}
        for company_id in request.company_ids:
            indicator = (
                db.query(FinancialIndicator)
                .filter(FinancialIndicator.company_id == company_id)
                .order_by(desc(FinancialIndicator.calculation_date))
                .first()
            )
            indicators[company_id] = indicator

        # Determine which metrics to include
        if request.metrics:
            metrics_to_include = request.metrics
        else:
            metrics_to_include = []
            for category_metrics in CompareService.AVAILABLE_METRICS.values():
                metrics_to_include.extend(category_metrics)

        # Build comparison data
        comparison_data = []
        metric_values = {metric: [] for metric in metrics_to_include}
        
        for company in companies:
            indicator = indicators.get(company.id)
            
            company_data = CompanyComparisonData(
                company_id=company.id,
                ticker_symbol=company.ticker_symbol,
                company_name_jp=company.company_name_jp,
                company_name_en=company.company_name_en,
                market_division=company.market_division,
                industry_name=company.industry_name,
                market_cap=company.market_cap,
                employee_count=company.employee_count
            )
            
            # Add financial indicators by category
            if indicator:
                for category, metrics in CompareService.AVAILABLE_METRICS.items():
                    category_data = {}
                    for metric in metrics:
                        value = getattr(indicator, metric, None)
                        category_data[metric] = value
                        
                        # Collect values for ranking and summary
                        if metric in metrics_to_include and value is not None:
                            metric_values[metric].append((company.id, value))
                    
                    setattr(company_data, category, category_data)
            
            comparison_data.append(company_data)

        # Calculate rankings if requested
        if request.include_rankings:
            rankings = CompareService._calculate_rankings(metric_values)
            for company_data in comparison_data:
                company_data.rankings = rankings.get(company_data.company_id, {})

        # Generate summary
        summary = CompareService._generate_summary(
            comparison_data, 
            metric_values, 
            metrics_to_include
        )

        return comparison_data, summary

    @staticmethod
    def _calculate_rankings(metric_values: Dict[str, List[tuple]]) -> Dict[int, Dict[str, int]]:
        """Calculate rankings for each metric"""
        company_rankings = {}
        
        for metric, values in metric_values.items():
            if not values:
                continue
                
            # Sort by value (descending for higher-is-better metrics, ascending for others)
            reverse_sort = metric in CompareService.HIGHER_IS_BETTER
            sorted_values = sorted(values, key=lambda x: x[1], reverse=reverse_sort)
            
            # Assign rankings
            for rank, (company_id, value) in enumerate(sorted_values, 1):
                if company_id not in company_rankings:
                    company_rankings[company_id] = {}
                company_rankings[company_id][metric] = rank
        
        return company_rankings

    @staticmethod
    def _generate_summary(
        comparison_data: List[CompanyComparisonData],
        metric_values: Dict[str, List[tuple]],
        metrics_to_include: List[str]
    ) -> ComparisonSummary:
        """Generate comparison summary statistics"""
        
        best_performers = {}
        worst_performers = {}
        averages = {}
        
        for metric in metrics_to_include:
            values = metric_values.get(metric, [])
            if not values:
                continue
            
            # Calculate average
            numeric_values = [v for _, v in values]
            averages[metric] = sum(numeric_values) / len(numeric_values)
            
            # Find best and worst performers
            if metric in CompareService.HIGHER_IS_BETTER:
                best_company_id, best_value = max(values, key=lambda x: x[1])
                worst_company_id, worst_value = min(values, key=lambda x: x[1])
            else:
                best_company_id, best_value = min(values, key=lambda x: x[1])
                worst_company_id, worst_value = max(values, key=lambda x: x[1])
            
            # Find company data for best/worst
            best_company = next(c for c in comparison_data if c.company_id == best_company_id)
            worst_company = next(c for c in comparison_data if c.company_id == worst_company_id)
            
            best_performers[metric] = {
                "company_id": best_company_id,
                "company_name": best_company.company_name_jp,
                "ticker_symbol": best_company.ticker_symbol,
                "value": best_value
            }
            
            worst_performers[metric] = {
                "company_id": worst_company_id,
                "company_name": worst_company.company_name_jp,
                "ticker_symbol": worst_company.ticker_symbol,
                "value": worst_value
            }

        return ComparisonSummary(
            total_companies=len(comparison_data),
            metrics_compared=metrics_to_include,
            best_performers=best_performers,
            worst_performers=worst_performers,
            averages=averages
        )

    @staticmethod
    def get_comparison_templates() -> List[ComparisonTemplate]:
        """Get predefined comparison templates"""
        templates = [
            ComparisonTemplate(
                id="profitability_analysis",
                name="収益性分析",
                description="ROE、ROA、各種利益率による収益性比較",
                category="profitability",
                metrics=["roe", "roa", "operating_margin", "net_margin", "gross_margin"]
            ),
            ComparisonTemplate(
                id="financial_safety",
                name="財務安全性分析",
                description="自己資本比率、流動比率等による財務安全性比較",
                category="safety",
                metrics=["equity_ratio", "debt_to_equity", "current_ratio", "quick_ratio"]
            ),
            ComparisonTemplate(
                id="valuation_metrics",
                name="株価指標比較",
                description="PER、PBR、配当利回り等による投資指標比較",
                category="valuation",
                metrics=["per", "pbr", "dividend_yield", "ev_ebitda"]
            ),
            ComparisonTemplate(
                id="growth_analysis",
                name="成長性分析",
                description="売上・利益成長率による成長性比較",
                category="growth",
                metrics=["revenue_growth", "income_growth", "asset_growth", "equity_growth"]
            ),
            ComparisonTemplate(
                id="efficiency_metrics",
                name="効率性分析",
                description="資産回転率等による経営効率性比較",
                category="efficiency",
                metrics=["asset_turnover", "inventory_turnover", "receivables_turnover"]
            ),
            ComparisonTemplate(
                id="comprehensive",
                name="総合分析",
                description="主要指標による総合的な企業比較",
                category="comprehensive",
                metrics=[
                    "roe", "roa", "operating_margin", "equity_ratio", "current_ratio",
                    "per", "pbr", "dividend_yield", "revenue_growth", "income_growth"
                ]
            )
        ]
        return templates

    @staticmethod
    def get_available_metrics() -> List[MetricInfo]:
        """Get information about available comparison metrics"""
        metric_info = {
            # Profitability metrics
            "roe": MetricInfo(metric="roe", label="ROE", category="profitability", unit="%", description="自己資本利益率", higher_is_better=True),
            "roa": MetricInfo(metric="roa", label="ROA", category="profitability", unit="%", description="総資産利益率", higher_is_better=True),
            "operating_margin": MetricInfo(metric="operating_margin", label="営業利益率", category="profitability", unit="%", description="営業利益率", higher_is_better=True),
            "net_margin": MetricInfo(metric="net_margin", label="当期純利益率", category="profitability", unit="%", description="当期純利益率", higher_is_better=True),
            "gross_margin": MetricInfo(metric="gross_margin", label="売上総利益率", category="profitability", unit="%", description="売上総利益率", higher_is_better=True),
            
            # Safety metrics
            "equity_ratio": MetricInfo(metric="equity_ratio", label="自己資本比率", category="safety", unit="%", description="自己資本比率", higher_is_better=True),
            "debt_to_equity": MetricInfo(metric="debt_to_equity", label="負債自己資本比率", category="safety", unit="倍", description="負債自己資本比率", higher_is_better=False),
            "current_ratio": MetricInfo(metric="current_ratio", label="流動比率", category="safety", unit="%", description="流動比率", higher_is_better=True),
            "quick_ratio": MetricInfo(metric="quick_ratio", label="当座比率", category="safety", unit="%", description="当座比率", higher_is_better=True),
            
            # Valuation metrics
            "per": MetricInfo(metric="per", label="PER", category="valuation", unit="倍", description="株価収益率", higher_is_better=False),
            "pbr": MetricInfo(metric="pbr", label="PBR", category="valuation", unit="倍", description="株価純資産倍率", higher_is_better=False),
            "dividend_yield": MetricInfo(metric="dividend_yield", label="配当利回り", category="valuation", unit="%", description="配当利回り", higher_is_better=True),
            "ev_ebitda": MetricInfo(metric="ev_ebitda", label="EV/EBITDA", category="valuation", unit="倍", description="EV/EBITDA倍率", higher_is_better=False),
            
            # Growth metrics
            "revenue_growth": MetricInfo(metric="revenue_growth", label="売上成長率", category="growth", unit="%", description="売上成長率", higher_is_better=True),
            "income_growth": MetricInfo(metric="income_growth", label="利益成長率", category="growth", unit="%", description="当期純利益成長率", higher_is_better=True),
            "asset_growth": MetricInfo(metric="asset_growth", label="総資産成長率", category="growth", unit="%", description="総資産成長率", higher_is_better=True),
            
            # Efficiency metrics
            "asset_turnover": MetricInfo(metric="asset_turnover", label="総資産回転率", category="efficiency", unit="回", description="総資産回転率", higher_is_better=True),
            "inventory_turnover": MetricInfo(metric="inventory_turnover", label="棚卸資産回転率", category="efficiency", unit="回", description="棚卸資産回転率", higher_is_better=True),
        }
        
        return list(metric_info.values())