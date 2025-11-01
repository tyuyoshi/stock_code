"""
Test suite for Financial Indicators Calculation Engine
"""

import pytest
from decimal import Decimal
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.financial_indicators import FinancialIndicatorEngine, IndustryType


class TestFinancialIndicatorEngine:
    """Test cases for the Financial Indicator Engine"""
    
    @pytest.fixture
    def engine(self):
        """Create a financial indicator engine instance"""
        return FinancialIndicatorEngine()
    
    @pytest.fixture
    def sample_financial_data(self):
        """Sample financial statement data for testing"""
        return {
            'revenue': 1000000000,  # 10億円
            'cost_of_revenue': 600000000,
            'gross_profit': 400000000,
            'operating_expenses': 250000000,
            'operating_income': 150000000,
            'net_income': 100000000,
            'total_assets': 2000000000,
            'current_assets': 800000000,
            'fixed_assets': 1200000000,
            'inventory': 200000000,
            'accounts_receivable': 150000000,
            'cash_and_equivalents': 300000000,
            'total_liabilities': 1200000000,
            'current_liabilities': 500000000,
            'long_term_liabilities': 700000000,
            'accounts_payable': 100000000,
            'shareholders_equity': 800000000,
            'operating_cash_flow': 120000000,
            'investing_cash_flow': -80000000,
            'financing_cash_flow': -30000000,
            'capital_expenditures': 50000000,
            'depreciation': 30000000,
            'amortization': 10000000,
            'interest_expense': 20000000
        }
    
    @pytest.fixture
    def sample_stock_data(self):
        """Sample stock market data for testing"""
        return {
            'close_price': 2500,  # 2,500円
            'shares_outstanding': 100000000,  # 1億株
            'annual_dividend': 50  # 50円/株
        }
    
    @pytest.fixture
    def previous_financial_data(self):
        """Previous period financial data for growth calculations"""
        return {
            'revenue': 900000000,
            'operating_income': 120000000,
            'net_income': 80000000,
            'total_assets': 1800000000,
            'shareholders_equity': 700000000
        }
    
    def test_profitability_indicators(self, engine, sample_financial_data):
        """Test profitability indicator calculations"""
        indicators = engine.calculate_profitability_indicators(sample_financial_data)
        
        # Test ROE
        assert 'roe' in indicators
        expected_roe = (100000000 / 800000000) * 100
        assert abs(indicators['roe'] - expected_roe) < 0.01
        
        # Test ROA
        assert 'roa' in indicators
        expected_roa = (100000000 / 2000000000) * 100
        assert abs(indicators['roa'] - expected_roa) < 0.01
        
        # Test Operating Margin
        assert 'operating_margin' in indicators
        expected_margin = (150000000 / 1000000000) * 100
        assert abs(indicators['operating_margin'] - expected_margin) < 0.01
        
        # Test ROIC
        assert 'roic' in indicators
        invested_capital = 2000000000 - 500000000
        nopat = 150000000 * 0.7  # 30% tax rate
        expected_roic = (nopat / invested_capital) * 100
        assert abs(indicators['roic'] - expected_roic) < 0.01
        
        # Test EBITDA
        assert 'ebitda' in indicators
        expected_ebitda = 150000000 + 30000000 + 10000000
        assert indicators['ebitda'] == expected_ebitda
    
    def test_safety_indicators(self, engine, sample_financial_data):
        """Test safety indicator calculations"""
        indicators = engine.calculate_safety_indicators(sample_financial_data)
        
        # Test Current Ratio
        assert 'current_ratio' in indicators
        expected_current = 800000000 / 500000000
        assert abs(indicators['current_ratio'] - expected_current) < 0.01
        
        # Test Quick Ratio
        assert 'quick_ratio' in indicators
        quick_assets = 800000000 - 200000000
        expected_quick = quick_assets / 500000000
        assert abs(indicators['quick_ratio'] - expected_quick) < 0.01
        
        # Test Debt to Equity
        assert 'debt_to_equity' in indicators
        expected_de = 1200000000 / 800000000
        assert abs(indicators['debt_to_equity'] - expected_de) < 0.01
        
        # Test Equity Ratio
        assert 'equity_ratio' in indicators
        expected_equity = (800000000 / 2000000000) * 100
        assert abs(indicators['equity_ratio'] - expected_equity) < 0.01
        
        # Test Interest Coverage
        assert 'interest_coverage' in indicators
        expected_coverage = 150000000 / 20000000
        assert abs(indicators['interest_coverage'] - expected_coverage) < 0.01
    
    def test_efficiency_indicators(self, engine, sample_financial_data):
        """Test efficiency indicator calculations"""
        indicators = engine.calculate_efficiency_indicators(sample_financial_data)
        
        # Test Asset Turnover
        assert 'asset_turnover' in indicators
        expected_turnover = 1000000000 / 2000000000
        assert abs(indicators['asset_turnover'] - expected_turnover) < 0.01
        
        # Test Receivables Turnover
        assert 'receivables_turnover' in indicators
        expected_receivables = 1000000000 / 150000000
        assert abs(indicators['receivables_turnover'] - expected_receivables) < 0.01
        
        # Test Days Sales Outstanding
        assert 'days_sales_outstanding' in indicators
        expected_dso = 365 / indicators['receivables_turnover']
        assert abs(indicators['days_sales_outstanding'] - expected_dso) < 0.01
        
        # Test Cash Conversion Cycle
        assert 'cash_conversion_cycle' in indicators
        assert isinstance(indicators['cash_conversion_cycle'], (int, float))
    
    def test_growth_indicators(self, engine, sample_financial_data, previous_financial_data):
        """Test growth indicator calculations"""
        indicators = engine.calculate_growth_indicators(
            sample_financial_data, 
            previous_financial_data
        )
        
        # Test Revenue Growth
        assert 'revenue_growth' in indicators
        expected_growth = ((1000000000 - 900000000) / 900000000) * 100
        assert abs(indicators['revenue_growth'] - expected_growth) < 0.01
        
        # Test Net Income Growth
        assert 'net_income_growth' in indicators
        expected_ni_growth = ((100000000 - 80000000) / 80000000) * 100
        assert abs(indicators['net_income_growth'] - expected_ni_growth) < 0.01
        
        # Test Operating Income Growth
        assert 'operating_income_growth' in indicators
        expected_oi_growth = ((150000000 - 120000000) / 120000000) * 100
        assert abs(indicators['operating_income_growth'] - expected_oi_growth) < 0.01
    
    def test_valuation_indicators(self, engine, sample_financial_data, sample_stock_data):
        """Test valuation indicator calculations"""
        indicators = engine.calculate_valuation_indicators(
            sample_financial_data,
            sample_stock_data
        )
        
        # Test Market Cap
        assert 'market_cap' in indicators
        expected_cap = 2500 * 100000000
        assert indicators['market_cap'] == expected_cap
        
        # Test PER
        assert 'per' in indicators
        eps = 100000000 / 100000000
        expected_per = 2500 / eps
        assert abs(indicators['per'] - expected_per) < 0.01
        
        # Test PBR
        assert 'pbr' in indicators
        bps = 800000000 / 100000000
        expected_pbr = 2500 / bps
        assert abs(indicators['pbr'] - expected_pbr) < 0.01
        
        # Test Dividend Yield
        assert 'dividend_yield' in indicators
        expected_yield = (50 / 2500) * 100
        assert abs(indicators['dividend_yield'] - expected_yield) < 0.01
    
    def test_cash_flow_indicators(self, engine, sample_financial_data):
        """Test cash flow indicator calculations"""
        indicators = engine.calculate_cash_flow_indicators(sample_financial_data)
        
        # Test Operating Cash Flow Ratio
        assert 'operating_cash_flow_ratio' in indicators
        expected_ratio = 120000000 / 500000000
        assert abs(indicators['operating_cash_flow_ratio'] - expected_ratio) < 0.01
        
        # Test Free Cash Flow
        assert 'free_cash_flow' in indicators
        expected_fcf = 120000000 - 50000000
        assert indicators['free_cash_flow'] == expected_fcf
        
        # Test FCF Margin
        assert 'fcf_margin' in indicators
        expected_margin = (expected_fcf / 1000000000) * 100
        assert abs(indicators['fcf_margin'] - expected_margin) < 0.01
        
        # Test Quality of Earnings
        assert 'quality_of_earnings' in indicators
        expected_quality = 120000000 / 100000000
        assert abs(indicators['quality_of_earnings'] - expected_quality) < 0.01
    
    def test_edge_cases(self, engine):
        """Test edge cases and error handling"""
        
        # Test with zero values
        zero_data = {
            'revenue': 0,
            'net_income': 100000,
            'shareholders_equity': 0,
            'total_assets': 1000000
        }
        indicators = engine.calculate_profitability_indicators(zero_data)
        assert indicators.get('roe') is None  # Division by zero should return None
        
        # Test with negative values
        negative_data = {
            'revenue': 1000000,
            'net_income': -50000,
            'shareholders_equity': 800000,
            'total_assets': 1000000
        }
        indicators = engine.calculate_profitability_indicators(negative_data)
        assert 'roe' in indicators
        assert indicators['roe'] < 0  # Negative ROE for loss-making company
        
        # Test with missing data
        incomplete_data = {
            'revenue': 1000000,
            'net_income': 100000
        }
        indicators = engine.calculate_profitability_indicators(incomplete_data)
        assert 'roe' not in indicators  # Should not calculate without required data
    
    def test_industry_adjustments(self, engine, sample_financial_data, sample_stock_data):
        """Test industry-specific adjustments"""
        
        # Test technology industry adjustments
        indicators = engine.calculate_all_indicators(
            sample_financial_data,
            sample_stock_data,
            industry_type=IndustryType.TECHNOLOGY
        )
        
        assert 'industry_adjustments' in indicators
        assert indicators['industry_adjustments']['industry_type'] == 'technology'
        
        # Check if adjusted PER is calculated for tech companies
        if 'adjusted_per' in indicators.get('valuation', {}):
            assert indicators['valuation']['adjusted_per'] < indicators['valuation']['per']
    
    def test_quality_scores(self, engine, sample_financial_data, sample_stock_data, previous_financial_data):
        """Test quality score calculations"""
        indicators = engine.calculate_all_indicators(
            sample_financial_data,
            sample_stock_data,
            previous_financial_data
        )
        
        quality_scores = indicators['quality_scores']
        
        # Check all quality scores are present
        assert 'profitability_score' in quality_scores
        assert 'safety_score' in quality_scores
        assert 'efficiency_score' in quality_scores
        assert 'growth_score' in quality_scores
        assert 'overall_quality_score' in quality_scores
        
        # Check scores are within valid range (0-100)
        for score_name, score_value in quality_scores.items():
            assert 0 <= score_value <= 100
        
        # Overall score should be weighted average
        assert quality_scores['overall_quality_score'] > 0
    
    def test_cagr_calculation(self, engine):
        """Test CAGR calculation"""
        indicators = engine.calculate_growth_indicators(
            {'revenue': 1500000000, 'net_income': 150000000},
            {'revenue': 1000000000, 'net_income': 100000000},
            periods=3
        )
        
        assert 'revenue_cagr' in indicators
        assert 'net_income_cagr' in indicators
        
        # Verify CAGR calculation
        expected_revenue_cagr = (pow(1500000000 / 1000000000, 1/3) - 1) * 100
        assert abs(indicators['revenue_cagr'] - expected_revenue_cagr) < 0.1
    
    def test_comprehensive_calculation(self, engine, sample_financial_data, sample_stock_data, previous_financial_data):
        """Test comprehensive indicator calculation"""
        indicators = engine.calculate_all_indicators(
            sample_financial_data,
            sample_stock_data,
            previous_financial_data,
            IndustryType.MANUFACTURING
        )
        
        # Check all main categories are present
        assert 'timestamp' in indicators
        assert 'profitability' in indicators
        assert 'safety' in indicators
        assert 'efficiency' in indicators
        assert 'growth' in indicators
        assert 'valuation' in indicators
        assert 'cash_flow' in indicators
        assert 'quality_scores' in indicators
        assert 'industry_adjustments' in indicators
        
        # Check timestamp format
        assert datetime.fromisoformat(indicators['timestamp'])
        
        # Verify at least some indicators in each category
        assert len(indicators['profitability']) > 0
        assert len(indicators['safety']) > 0
        assert len(indicators['efficiency']) > 0
        assert len(indicators['growth']) > 0
        assert len(indicators['valuation']) > 0
        assert len(indicators['cash_flow']) > 0
    
    def test_indicator_descriptions(self, engine):
        """Test indicator description retrieval"""
        description = engine.get_indicator_description('roe')
        assert 'Return on Equity' in description
        assert '自己資本利益率' in description
        
        description = engine.get_indicator_description('per')
        assert 'Price to Earnings' in description
        assert '株価収益率' in description
        
        # Test unknown indicator
        description = engine.get_indicator_description('unknown_indicator')
        assert 'No description available' in description


if __name__ == "__main__":
    pytest.main([__file__, "-v"])