"""
Financial Indicators Calculation Engine
Advanced financial metrics and ratios calculation for Japanese listed companies
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional, List, Any
from enum import Enum
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class IndustryType(Enum):
    """Industry classification for adjustment logic"""
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    REAL_ESTATE = "real_estate"
    SERVICE = "service"
    UTILITIES = "utilities"
    HEALTHCARE = "healthcare"
    CONSUMER_GOODS = "consumer_goods"
    OTHER = "other"


class FinancialIndicatorEngine:
    """
    Advanced financial indicator calculation engine
    Implements comprehensive financial metrics for investment analysis
    """
    
    def __init__(self, tax_rate: float = 0.3, benchmarks: Optional[Dict[str, Dict[str, float]]] = None):
        """Initialize the financial indicator engine
        
        Args:
            tax_rate: Corporate tax rate (default: 0.3 for 30%)
            benchmarks: Custom benchmark values for quality scoring
        """
        self._cache = {}
        self._precision = 4  # Decimal places for calculations
        self.tax_rate = tax_rate
        self.custom_benchmarks = benchmarks or {}
        
    def calculate_all_indicators(
        self, 
        financial_data: Dict[str, float],
        stock_data: Optional[Dict[str, float]] = None,
        previous_data: Optional[Dict[str, float]] = None,
        industry_type: Optional[IndustryType] = None
    ) -> Dict[str, Any]:
        """
        Calculate all available financial indicators
        
        Args:
            financial_data: Current period financial statement data
            stock_data: Stock price and market data
            previous_data: Previous period financial data for growth calculations
            industry_type: Industry classification for adjusted calculations
            
        Returns:
            Dictionary containing all calculated indicators
        """
        indicators = {
            "timestamp": datetime.now().isoformat(),
            "profitability": {},
            "safety": {},
            "efficiency": {},
            "growth": {},
            "valuation": {},
            "cash_flow": {},
            "quality_scores": {}
        }
        
        # Calculate each category of indicators
        indicators["profitability"] = self.calculate_profitability_indicators(financial_data)
        indicators["safety"] = self.calculate_safety_indicators(financial_data)
        indicators["efficiency"] = self.calculate_efficiency_indicators(financial_data)
        
        if previous_data:
            indicators["growth"] = self.calculate_growth_indicators(financial_data, previous_data)
        
        if stock_data:
            indicators["valuation"] = self.calculate_valuation_indicators(
                financial_data, stock_data, previous_data
            )
        
        indicators["cash_flow"] = self.calculate_cash_flow_indicators(financial_data)
        
        # Apply industry adjustments if specified
        if industry_type:
            indicators = self._apply_industry_adjustments(indicators, industry_type)
        
        # Calculate quality scores
        indicators["quality_scores"] = self._calculate_quality_scores(indicators)
        
        return indicators
    
    def calculate_profitability_indicators(self, data: Dict[str, float]) -> Dict[str, Optional[float]]:
        """
        Calculate profitability indicators
        """
        indicators = {}
        
        try:
            # ROE (Return on Equity) - 自己資本利益率
            if self._has_values(data, ['net_income', 'shareholders_equity']):
                indicators['roe'] = self._safe_divide(
                    data['net_income'], 
                    data['shareholders_equity']
                ) * 100
            
            # ROA (Return on Assets) - 総資産利益率
            if self._has_values(data, ['net_income', 'total_assets']):
                indicators['roa'] = self._safe_divide(
                    data['net_income'], 
                    data['total_assets']
                ) * 100
            
            # ROIC (Return on Invested Capital) - 投下資本利益率
            if self._has_values(data, ['operating_income', 'total_assets', 'current_liabilities']):
                invested_capital = data['total_assets'] - data['current_liabilities']
                if invested_capital > 0:
                    # Apply configurable tax rate
                    nopat = data['operating_income'] * (1 - self.tax_rate)
                    indicators['roic'] = self._safe_divide(nopat, invested_capital) * 100
            
            # Operating Margin - 営業利益率
            if self._has_values(data, ['operating_income', 'revenue']):
                indicators['operating_margin'] = self._safe_divide(
                    data['operating_income'], 
                    data['revenue']
                ) * 100
            
            # Net Profit Margin - 純利益率
            if self._has_values(data, ['net_income', 'revenue']):
                indicators['net_margin'] = self._safe_divide(
                    data['net_income'], 
                    data['revenue']
                ) * 100
            
            # Gross Margin - 売上総利益率
            if self._has_values(data, ['gross_profit', 'revenue']):
                indicators['gross_margin'] = self._safe_divide(
                    data['gross_profit'], 
                    data['revenue']
                ) * 100
            
            # EBITDA and EBITDA Margin
            if self._has_values(data, ['operating_income', 'depreciation', 'amortization']):
                ebitda = data['operating_income'] + data.get('depreciation', 0) + data.get('amortization', 0)
                indicators['ebitda'] = ebitda
                
                if data.get('revenue'):
                    indicators['ebitda_margin'] = self._safe_divide(ebitda, data['revenue']) * 100
            
        except Exception as e:
            logger.error(f"Error calculating profitability indicators: {e}")
        
        return indicators
    
    def calculate_safety_indicators(self, data: Dict[str, float]) -> Dict[str, Optional[float]]:
        """
        Calculate safety/solvency indicators
        """
        indicators = {}
        
        try:
            # Current Ratio - 流動比率
            if self._has_values(data, ['current_assets', 'current_liabilities']):
                indicators['current_ratio'] = self._safe_divide(
                    data['current_assets'], 
                    data['current_liabilities']
                )
            
            # Quick Ratio (Acid Test) - 当座比率
            if self._has_values(data, ['current_assets', 'inventory', 'current_liabilities']):
                quick_assets = data['current_assets'] - data.get('inventory', 0)
                indicators['quick_ratio'] = self._safe_divide(
                    quick_assets, 
                    data['current_liabilities']
                )
            
            # Debt to Equity Ratio - 負債資本比率
            if self._has_values(data, ['total_liabilities', 'shareholders_equity']):
                indicators['debt_to_equity'] = self._safe_divide(
                    data['total_liabilities'], 
                    data['shareholders_equity']
                )
            
            # Equity Ratio - 自己資本比率
            if self._has_values(data, ['shareholders_equity', 'total_assets']):
                indicators['equity_ratio'] = self._safe_divide(
                    data['shareholders_equity'], 
                    data['total_assets']
                ) * 100
            
            # Interest Coverage Ratio - インタレスト・カバレッジ・レシオ
            if self._has_values(data, ['operating_income', 'interest_expense']):
                if data.get('interest_expense', 0) > 0:
                    indicators['interest_coverage'] = self._safe_divide(
                        data['operating_income'], 
                        data['interest_expense']
                    )
            
            # Fixed Asset Ratio - 固定比率
            if self._has_values(data, ['fixed_assets', 'shareholders_equity']):
                indicators['fixed_asset_ratio'] = self._safe_divide(
                    data['fixed_assets'], 
                    data['shareholders_equity']
                ) * 100
            
            # Fixed Long-term Fitness Ratio - 固定長期適合率
            if self._has_values(data, ['fixed_assets', 'shareholders_equity', 'long_term_liabilities']):
                long_term_capital = data['shareholders_equity'] + data.get('long_term_liabilities', 0)
                indicators['fixed_long_term_fitness_ratio'] = self._safe_divide(
                    data['fixed_assets'], 
                    long_term_capital
                ) * 100
            
        except Exception as e:
            logger.error(f"Error calculating safety indicators: {e}")
        
        return indicators
    
    def calculate_efficiency_indicators(self, data: Dict[str, float]) -> Dict[str, Optional[float]]:
        """
        Calculate efficiency/activity indicators
        """
        indicators = {}
        
        try:
            # Total Asset Turnover - 総資産回転率
            if self._has_values(data, ['revenue', 'total_assets']):
                indicators['asset_turnover'] = self._safe_divide(
                    data['revenue'], 
                    data['total_assets']
                )
            
            # Receivables Turnover - 売上債権回転率
            if self._has_values(data, ['revenue', 'accounts_receivable']):
                indicators['receivables_turnover'] = self._safe_divide(
                    data['revenue'], 
                    data['accounts_receivable']
                )
                # Days Sales Outstanding (DSO) - 売上債権回転日数
                indicators['days_sales_outstanding'] = self._safe_divide(
                    365, 
                    indicators['receivables_turnover']
                )
            
            # Inventory Turnover - 棚卸資産回転率
            if self._has_values(data, ['cost_of_revenue', 'inventory']):
                indicators['inventory_turnover'] = self._safe_divide(
                    data['cost_of_revenue'], 
                    data['inventory']
                )
                # Days Inventory Outstanding (DIO) - 棚卸資産回転日数
                indicators['days_inventory_outstanding'] = self._safe_divide(
                    365, 
                    indicators['inventory_turnover']
                )
            
            # Payables Turnover - 買入債務回転率
            if self._has_values(data, ['cost_of_revenue', 'accounts_payable']):
                indicators['payables_turnover'] = self._safe_divide(
                    data['cost_of_revenue'], 
                    data['accounts_payable']
                )
                # Days Payables Outstanding (DPO) - 買入債務回転日数
                indicators['days_payables_outstanding'] = self._safe_divide(
                    365, 
                    indicators['payables_turnover']
                )
            
            # Cash Conversion Cycle (CCC) - キャッシュ・コンバージョン・サイクル
            if all(key in indicators for key in ['days_sales_outstanding', 'days_inventory_outstanding', 'days_payables_outstanding']):
                indicators['cash_conversion_cycle'] = (
                    indicators['days_sales_outstanding'] + 
                    indicators['days_inventory_outstanding'] - 
                    indicators['days_payables_outstanding']
                )
            
            # Working Capital Turnover - 運転資本回転率
            if self._has_values(data, ['revenue', 'current_assets', 'current_liabilities']):
                working_capital = data['current_assets'] - data['current_liabilities']
                if working_capital > 0:
                    indicators['working_capital_turnover'] = self._safe_divide(
                        data['revenue'], 
                        working_capital
                    )
            
        except Exception as e:
            logger.error(f"Error calculating efficiency indicators: {e}")
        
        return indicators
    
    def calculate_growth_indicators(
        self, 
        current_data: Dict[str, float], 
        previous_data: Dict[str, float],
        periods: int = 1
    ) -> Dict[str, Optional[float]]:
        """
        Calculate growth indicators
        """
        indicators = {}
        
        try:
            # Revenue Growth Rate - 売上高成長率
            if self._has_values(current_data, ['revenue']) and self._has_values(previous_data, ['revenue']):
                indicators['revenue_growth'] = self._calculate_growth_rate(
                    previous_data['revenue'], 
                    current_data['revenue']
                )
            
            # Operating Income Growth Rate - 営業利益成長率
            if self._has_values(current_data, ['operating_income']) and self._has_values(previous_data, ['operating_income']):
                indicators['operating_income_growth'] = self._calculate_growth_rate(
                    previous_data['operating_income'], 
                    current_data['operating_income']
                )
            
            # Net Income Growth Rate - 純利益成長率
            if self._has_values(current_data, ['net_income']) and self._has_values(previous_data, ['net_income']):
                indicators['net_income_growth'] = self._calculate_growth_rate(
                    previous_data['net_income'], 
                    current_data['net_income']
                )
            
            # Total Assets Growth Rate - 総資産成長率
            if self._has_values(current_data, ['total_assets']) and self._has_values(previous_data, ['total_assets']):
                indicators['asset_growth'] = self._calculate_growth_rate(
                    previous_data['total_assets'], 
                    current_data['total_assets']
                )
            
            # Equity Growth Rate - 自己資本成長率
            if self._has_values(current_data, ['shareholders_equity']) and self._has_values(previous_data, ['shareholders_equity']):
                indicators['equity_growth'] = self._calculate_growth_rate(
                    previous_data['shareholders_equity'], 
                    current_data['shareholders_equity']
                )
            
            # CAGR (Compound Annual Growth Rate) - 年平均成長率
            if periods > 1:
                if self._has_values(current_data, ['revenue']) and self._has_values(previous_data, ['revenue']):
                    indicators['revenue_cagr'] = self._calculate_cagr(
                        previous_data['revenue'], 
                        current_data['revenue'], 
                        periods
                    )
                
                if self._has_values(current_data, ['net_income']) and self._has_values(previous_data, ['net_income']):
                    indicators['net_income_cagr'] = self._calculate_cagr(
                        previous_data['net_income'], 
                        current_data['net_income'], 
                        periods
                    )
            
        except Exception as e:
            logger.error(f"Error calculating growth indicators: {e}")
        
        return indicators
    
    def calculate_valuation_indicators(
        self, 
        financial_data: Dict[str, float],
        stock_data: Dict[str, float],
        previous_data: Optional[Dict[str, float]] = None
    ) -> Dict[str, Optional[float]]:
        """
        Calculate valuation indicators
        """
        indicators = {}
        
        try:
            stock_price = stock_data.get('close_price', 0)
            shares_outstanding = stock_data.get('shares_outstanding', 0)
            
            if stock_price and shares_outstanding:
                market_cap = stock_price * shares_outstanding
                indicators['market_cap'] = market_cap
                
                # PER (Price to Earnings Ratio) - 株価収益率
                if self._has_values(financial_data, ['net_income']):
                    eps = self._safe_divide(financial_data['net_income'], shares_outstanding)
                    if eps > 0:
                        indicators['per'] = self._safe_divide(stock_price, eps)
                        indicators['eps'] = eps
                
                # PBR (Price to Book Ratio) - 株価純資産倍率
                if self._has_values(financial_data, ['shareholders_equity']):
                    bps = self._safe_divide(financial_data['shareholders_equity'], shares_outstanding)
                    if bps > 0:
                        indicators['pbr'] = self._safe_divide(stock_price, bps)
                        indicators['bps'] = bps
                
                # PSR (Price to Sales Ratio) - 株価売上高倍率
                if self._has_values(financial_data, ['revenue']):
                    indicators['psr'] = self._safe_divide(market_cap, financial_data['revenue'])
                
                # PEG Ratio - PEGレシオ
                if 'per' in indicators and previous_data:
                    growth_indicators = self.calculate_growth_indicators(financial_data, previous_data)
                    earnings_growth = growth_indicators.get('net_income_growth')
                    if earnings_growth and earnings_growth > 0:
                        indicators['peg_ratio'] = self._safe_divide(indicators['per'], earnings_growth)
                
                # EV/EBITDA - 企業価値/EBITDA倍率
                if self._has_values(financial_data, ['operating_income', 'depreciation', 'amortization']):
                    ebitda = financial_data['operating_income'] + financial_data.get('depreciation', 0) + financial_data.get('amortization', 0)
                    
                    # Enterprise Value = Market Cap + Total Debt - Cash
                    total_debt = financial_data.get('total_liabilities', 0)
                    cash = financial_data.get('cash_and_equivalents', 0)
                    enterprise_value = market_cap + total_debt - cash
                    
                    if ebitda > 0:
                        indicators['ev_ebitda'] = self._safe_divide(enterprise_value, ebitda)
                        indicators['enterprise_value'] = enterprise_value
                
                # Dividend Yield - 配当利回り
                if stock_data.get('annual_dividend'):
                    indicators['dividend_yield'] = self._safe_divide(
                        stock_data['annual_dividend'], 
                        stock_price
                    ) * 100
                
                # Dividend Payout Ratio - 配当性向
                if stock_data.get('annual_dividend') and self._has_values(financial_data, ['net_income']):
                    total_dividends = stock_data['annual_dividend'] * shares_outstanding
                    indicators['payout_ratio'] = self._safe_divide(
                        total_dividends, 
                        financial_data['net_income']
                    ) * 100
                
        except Exception as e:
            logger.error(f"Error calculating valuation indicators: {e}")
        
        return indicators
    
    def calculate_cash_flow_indicators(self, data: Dict[str, float]) -> Dict[str, Optional[float]]:
        """
        Calculate cash flow indicators
        """
        indicators = {}
        
        try:
            # Operating Cash Flow Ratio - 営業キャッシュフロー比率
            if self._has_values(data, ['operating_cash_flow', 'current_liabilities']):
                indicators['operating_cash_flow_ratio'] = self._safe_divide(
                    data['operating_cash_flow'], 
                    data['current_liabilities']
                )
            
            # Free Cash Flow - フリーキャッシュフロー
            if self._has_values(data, ['operating_cash_flow', 'capital_expenditures']):
                indicators['free_cash_flow'] = data['operating_cash_flow'] - data.get('capital_expenditures', 0)
                
                # FCF Margin - FCFマージン
                if data.get('revenue'):
                    indicators['fcf_margin'] = self._safe_divide(
                        indicators['free_cash_flow'], 
                        data['revenue']
                    ) * 100
            
            # Cash Flow to Debt Ratio - キャッシュフロー対負債比率
            if self._has_values(data, ['operating_cash_flow', 'total_liabilities']):
                indicators['cash_flow_to_debt'] = self._safe_divide(
                    data['operating_cash_flow'], 
                    data['total_liabilities']
                )
            
            # Quality of Earnings - 利益の質
            if self._has_values(data, ['operating_cash_flow', 'net_income']):
                indicators['quality_of_earnings'] = self._safe_divide(
                    data['operating_cash_flow'], 
                    data['net_income']
                )
            
            # Cash Return on Assets - キャッシュROA
            if self._has_values(data, ['operating_cash_flow', 'total_assets']):
                indicators['cash_roa'] = self._safe_divide(
                    data['operating_cash_flow'], 
                    data['total_assets']
                ) * 100
            
        except Exception as e:
            logger.error(f"Error calculating cash flow indicators: {e}")
        
        return indicators
    
    def _apply_industry_adjustments(
        self, 
        indicators: Dict[str, Any], 
        industry_type: IndustryType
    ) -> Dict[str, Any]:
        """
        Apply industry-specific adjustments to indicators
        """
        adjustments = {
            IndustryType.TECHNOLOGY: {
                'psr_weight': 1.2,  # Higher PSR tolerance for tech companies
                'per_weight': 1.3,  # Higher PER acceptable
                'rd_adjustment': True  # Consider R&D expenses
            },
            IndustryType.FINANCE: {
                'exclude_debt_ratios': True,  # Debt ratios less relevant for banks
                'focus_on_roe': True,  # ROE more important
                'capital_adequacy': True  # Add capital adequacy ratios
            },
            IndustryType.RETAIL: {
                'inventory_turnover_weight': 1.5,  # More important for retail
                'same_store_sales': True  # Consider same-store sales growth
            },
            IndustryType.MANUFACTURING: {
                'asset_turnover_weight': 1.3,  # Asset efficiency crucial
                'working_capital_focus': True  # Working capital management important
            },
            IndustryType.REAL_ESTATE: {
                'nav_focus': True,  # Net Asset Value important
                'rental_yield': True,  # Consider rental yields
                'depreciation_adjustment': True  # Adjust for depreciation policies
            },
            IndustryType.UTILITIES: {
                'stable_dividend_focus': True,  # Dividend stability important
                'regulatory_adjustment': True,  # Consider regulatory environment
                'capex_intensity': True  # High capex requirements
            }
        }
        
        adjustment_config = adjustments.get(industry_type, {})
        
        # Apply adjustments based on industry configuration
        if adjustment_config:
            indicators['industry_adjustments'] = {
                'industry_type': industry_type.value,
                'adjustments_applied': list(adjustment_config.keys())
            }
            
            # Example: Adjust PER for technology companies
            if industry_type == IndustryType.TECHNOLOGY and 'valuation' in indicators:
                if 'per' in indicators['valuation'] and indicators['valuation']['per']:
                    adjusted_per = indicators['valuation']['per'] / adjustment_config.get('per_weight', 1.0)
                    indicators['valuation']['adjusted_per'] = adjusted_per
        
        return indicators
    
    def _calculate_quality_scores(self, indicators: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate overall quality scores based on multiple indicators
        """
        scores = {}
        
        # Get default benchmarks or use custom ones
        default_benchmarks = {
            'profitability': {'roe': 15, 'roa': 5, 'operating_margin': 10, 'roic': 12},
            'safety': {'current_ratio': 1.5, 'equity_ratio': 40, 'interest_coverage': 3},
            'efficiency': {'asset_turnover': 1.0, 'cash_conversion_cycle': 60},
            'growth': {'revenue_growth': 10, 'net_income_growth': 15}
        }
        
        # Merge custom benchmarks with defaults
        benchmarks = default_benchmarks.copy()
        if self.custom_benchmarks:
            for category, values in self.custom_benchmarks.items():
                if category in benchmarks:
                    benchmarks[category].update(values)
        
        # Profitability Score
        profitability_metrics = ['roe', 'roa', 'operating_margin', 'roic']
        prof_score = self._calculate_category_score(
            indicators.get('profitability', {}), 
            profitability_metrics,
            benchmarks['profitability']
        )
        scores['profitability_score'] = prof_score
        
        # Safety Score
        safety_metrics = ['current_ratio', 'equity_ratio', 'interest_coverage']
        safety_score = self._calculate_category_score(
            indicators.get('safety', {}),
            safety_metrics,
            benchmarks['safety']
        )
        scores['safety_score'] = safety_score
        
        # Efficiency Score
        efficiency_metrics = ['asset_turnover', 'cash_conversion_cycle']
        efficiency_score = self._calculate_category_score(
            indicators.get('efficiency', {}),
            efficiency_metrics,
            benchmarks['efficiency']
        )
        scores['efficiency_score'] = efficiency_score
        
        # Growth Score
        if indicators.get('growth'):
            growth_metrics = ['revenue_growth', 'net_income_growth']
            growth_score = self._calculate_category_score(
                indicators.get('growth', {}),
                growth_metrics,
                benchmarks['growth']
            )
            scores['growth_score'] = growth_score
        
        # Overall Quality Score (weighted average)
        weights = {
            'profitability_score': 0.35,
            'safety_score': 0.25,
            'efficiency_score': 0.20,
            'growth_score': 0.20
        }
        
        overall_score = sum(
            scores.get(metric, 0) * weight 
            for metric, weight in weights.items()
        )
        scores['overall_quality_score'] = round(overall_score, 2)
        
        return scores
    
    def _calculate_category_score(
        self, 
        indicators: Dict[str, float], 
        metrics: List[str],
        benchmarks: Dict[str, float]
    ) -> float:
        """
        Calculate a category score based on metrics vs benchmarks
        """
        if not indicators:
            return 0.0
        
        scores = []
        for metric in metrics:
            if metric in indicators and metric in benchmarks:
                value = indicators[metric]
                benchmark = benchmarks[metric]
                
                if value is not None and benchmark != 0:
                    # For CCC, lower is better
                    if metric == 'cash_conversion_cycle':
                        score = min((benchmark / value) * 100, 100) if value > 0 else 100
                    else:
                        score = min((value / benchmark) * 100, 100)
                    scores.append(score)
        
        return round(sum(scores) / len(scores), 2) if scores else 0.0
    
    def _calculate_growth_rate(self, previous_value: float, current_value: float) -> Optional[float]:
        """
        Calculate growth rate between two periods
        """
        if previous_value == 0:
            return None if current_value == 0 else float('inf')
        
        growth_rate = ((current_value - previous_value) / abs(previous_value)) * 100
        return round(growth_rate, 2)
    
    def _calculate_cagr(self, initial_value: float, final_value: float, periods: int) -> Optional[float]:
        """
        Calculate Compound Annual Growth Rate
        """
        if initial_value <= 0 or final_value <= 0 or periods <= 0:
            return None
        
        cagr = (pow(final_value / initial_value, 1 / periods) - 1) * 100
        return round(cagr, 2)
    
    def _safe_divide(self, numerator: float, denominator: float) -> Optional[float]:
        """
        Safely divide two numbers, returning None if division by zero
        """
        if denominator == 0:
            return None
        
        result = Decimal(str(numerator)) / Decimal(str(denominator))
        return float(result.quantize(Decimal(f'0.{"0" * self._precision}'), rounding=ROUND_HALF_UP))
    
    def _has_values(self, data: Dict[str, float], keys: List[str]) -> bool:
        """
        Check if all required keys exist and have non-None values
        """
        return all(data.get(key) is not None for key in keys)
    
    def get_indicator_description(self, indicator_name: str) -> str:
        """
        Get a description of what an indicator means
        """
        descriptions = {
            'roe': 'Return on Equity - 自己資本利益率: Measures profitability relative to shareholders equity',
            'roa': 'Return on Assets - 総資産利益率: Measures how efficiently assets generate profit',
            'roic': 'Return on Invested Capital - 投下資本利益率: Measures return on all invested capital',
            'per': 'Price to Earnings Ratio - 株価収益率: Stock price relative to earnings per share',
            'pbr': 'Price to Book Ratio - 株価純資産倍率: Stock price relative to book value per share',
            'current_ratio': 'Current Ratio - 流動比率: Ability to pay short-term obligations',
            'equity_ratio': 'Equity Ratio - 自己資本比率: Proportion of equity to total assets',
            'asset_turnover': 'Asset Turnover - 総資産回転率: Efficiency in using assets to generate revenue',
            'cash_conversion_cycle': 'Cash Conversion Cycle - キャッシュ変換サイクル: Days to convert investments to cash',
        }
        
        return descriptions.get(indicator_name, f"No description available for {indicator_name}")