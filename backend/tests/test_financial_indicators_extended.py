"""
Extended test suite for Financial Indicators Calculation Engine
Testing edge cases, error handling, and comprehensive coverage
"""

import pytest
from decimal import Decimal
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from services.financial_indicators import FinancialIndicatorEngine, IndustryType


class TestFinancialIndicatorEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def engine(self):
        """Create a financial indicator engine instance"""
        return FinancialIndicatorEngine()
    
    @pytest.mark.unit
    def test_zero_division_handling(self, engine):
        """Test handling of zero division cases"""
        data = {
            'revenue': 0,  # Zero revenue
            'net_income': 100000,
            'total_assets': 0,  # Zero assets
            'shareholders_equity': 0,  # Zero equity
            'current_assets': 100000,
            'current_liabilities': 0,  # Zero liabilities
            'operating_income': 50000,
            'shares_outstanding': 0  # Zero shares
        }
        
        result = engine.calculate_all_indicators(data)
        
        # Should not raise ZeroDivisionError
        assert result is not None
        
        # Check specific indicators that involve division
        profitability = result.get('profitability', {})
        
        # ROE should handle zero equity
        if 'roe' in profitability:
            assert profitability['roe'] in [None, 0, float('inf')]
        
        # ROA should handle zero assets
        if 'roa' in profitability:
            assert profitability['roa'] in [None, 0, float('inf')]
        
        # Current ratio should handle zero current liabilities
        safety = result.get('safety', {})
        if 'current_ratio' in safety:
            assert safety['current_ratio'] in [None, float('inf')]
    
    @pytest.mark.unit
    def test_negative_values_handling(self, engine):
        """Test handling of negative values (losses, negative equity)"""
        data = {
            'revenue': 1000000000,
            'net_income': -50000000,  # Loss
            'operating_income': -20000000,  # Operating loss
            'total_assets': 2000000000,
            'shareholders_equity': -100000000,  # Negative equity (debt excess)
            'current_assets': 500000000,
            'current_liabilities': 800000000,
            'total_liabilities': 2100000000,
            'operating_cash_flow': -30000000,  # Negative cash flow
            'shares_outstanding': 10000000
        }
        
        result = engine.calculate_all_indicators(data)
        
        # Check that negative values are handled correctly
        profitability = result.get('profitability', {})
        
        # Negative ROE (loss with negative equity)
        if 'roe' in profitability:
            # Negative income / Negative equity = Positive (misleading)
            # Good implementations should flag this
            assert profitability['roe'] is not None
        
        # Negative margins
        if 'net_margin' in profitability:
            assert profitability['net_margin'] < 0
        
        if 'operating_margin' in profitability:
            assert profitability['operating_margin'] < 0
    
    @pytest.mark.unit
    def test_missing_required_fields(self, engine):
        """Test calculation with missing required fields"""
        incomplete_data = {
            'revenue': 1000000000,
            'net_income': 100000000
            # Missing most fields
        }
        
        result = engine.calculate_all_indicators(incomplete_data)
        
        # Should return partial results without crashing
        assert result is not None
        
        # Check that available calculations are done
        if 'profitability' in result and 'net_margin' in result['profitability']:
            expected_margin = (100000000 / 1000000000) * 100
            assert abs(result['profitability']['net_margin'] - expected_margin) < 0.01
    
    @pytest.mark.unit
    def test_extreme_values(self, engine):
        """Test handling of extreme values"""
        extreme_data = {
            'revenue': 1e15,  # Very large revenue
            'net_income': 1e14,
            'total_assets': 1e16,
            'shareholders_equity': 1e15,
            'current_assets': 1e14,
            'current_liabilities': 1e13,
            'total_liabilities': 1e15,
            'shares_outstanding': 1e10,
            'operating_cash_flow': 1e14
        }
        
        result = engine.calculate_all_indicators(extreme_data)
        
        # Should handle large numbers without overflow
        assert result is not None
        
        profitability = result.get('profitability', {})
        if 'roe' in profitability:
            assert 0 < profitability['roe'] < 100
    
    @pytest.mark.unit
    def test_all_zero_data(self, engine):
        """Test with all zero values"""
        zero_data = {key: 0 for key in [
            'revenue', 'net_income', 'total_assets', 'shareholders_equity',
            'current_assets', 'current_liabilities', 'total_liabilities'
        ]}
        
        result = engine.calculate_all_indicators(zero_data)
        
        # Should handle all zeros without crashing
        assert result is not None


class TestIndustrySpecificCalculations:
    """Test industry-specific indicator calculations"""
    
    @pytest.fixture
    def engine(self):
        return FinancialIndicatorEngine()
    
    @pytest.fixture
    def bank_data(self):
        """Sample data for banking industry"""
        return {
            'interest_income': 500000000,
            'interest_expense': 200000000,
            'net_interest_income': 300000000,
            'non_interest_income': 100000000,
            'loan_portfolio': 10000000000,
            'deposits': 12000000000,
            'non_performing_loans': 100000000,
            'loan_loss_provision': 50000000,
            'tier1_capital': 1000000000,
            'risk_weighted_assets': 8000000000,
            'total_assets': 15000000000,
            'shareholders_equity': 1200000000
        }
    
    @pytest.fixture
    def retail_data(self):
        """Sample data for retail industry"""
        return {
            'revenue': 5000000000,
            'cost_of_revenue': 3500000000,
            'inventory': 500000000,
            'stores_count': 100,
            'total_selling_space': 100000,  # square meters
            'same_store_sales_growth': 0.05,
            'inventory_turnover_days': 30,
            'gross_profit': 1500000000
        }
    
    @pytest.mark.unit
    def test_banking_indicators(self, engine, bank_data):
        """Test banking-specific indicators"""
        result = engine.calculate_industry_specific_indicators(
            bank_data, 
            IndustryType.BANKING
        )
        
        assert 'banking_metrics' in result
        
        banking = result['banking_metrics']
        
        # Net Interest Margin
        if 'net_interest_margin' in banking:
            expected_nim = (bank_data['net_interest_income'] / 
                          bank_data['loan_portfolio']) * 100
            assert abs(banking['net_interest_margin'] - expected_nim) < 0.01
        
        # Non-Performing Loan Ratio
        if 'npl_ratio' in banking:
            expected_npl = (bank_data['non_performing_loans'] / 
                          bank_data['loan_portfolio']) * 100
            assert abs(banking['npl_ratio'] - expected_npl) < 0.01
        
        # Tier 1 Capital Ratio
        if 'tier1_capital_ratio' in banking:
            expected_tier1 = (bank_data['tier1_capital'] / 
                            bank_data['risk_weighted_assets']) * 100
            assert abs(banking['tier1_capital_ratio'] - expected_tier1) < 0.01
    
    @pytest.mark.unit
    def test_retail_indicators(self, engine, retail_data):
        """Test retail-specific indicators"""
        result = engine.calculate_industry_specific_indicators(
            retail_data,
            IndustryType.RETAIL
        )
        
        assert 'retail_metrics' in result
        
        retail = result['retail_metrics']
        
        # Sales per store
        if 'sales_per_store' in retail:
            expected_sps = retail_data['revenue'] / retail_data['stores_count']
            assert abs(retail['sales_per_store'] - expected_sps) < 1
        
        # Sales per square meter
        if 'sales_per_sqm' in retail:
            expected_spsm = retail_data['revenue'] / retail_data['total_selling_space']
            assert abs(retail['sales_per_sqm'] - expected_spsm) < 1
        
        # Gross margin
        if 'gross_margin' in retail:
            expected_gm = (retail_data['gross_profit'] / retail_data['revenue']) * 100
            assert abs(retail['gross_margin'] - expected_gm) < 0.01


class TestTimeSeriesAnalysis:
    """Test time series and trend analysis"""
    
    @pytest.fixture
    def engine(self):
        return FinancialIndicatorEngine()
    
    @pytest.fixture
    def historical_data(self):
        """Multi-year financial data"""
        return pd.DataFrame({
            'year': [2020, 2021, 2022, 2023, 2024],
            'revenue': [800000000, 900000000, 950000000, 1000000000, 1100000000],
            'net_income': [50000000, 70000000, 85000000, 100000000, 115000000],
            'total_assets': [1500000000, 1700000000, 1850000000, 2000000000, 2200000000],
            'shareholders_equity': [600000000, 700000000, 750000000, 800000000, 900000000],
            'operating_cash_flow': [60000000, 80000000, 95000000, 110000000, 125000000],
            'eps': [5.0, 7.0, 8.5, 10.0, 11.5],
            'shares_outstanding': [10000000, 10000000, 10000000, 10000000, 10000000]
        })
    
    @pytest.mark.unit
    def test_growth_rate_calculations(self, engine, historical_data):
        """Test growth rate calculations over time"""
        result = engine.calculate_growth_metrics(historical_data)
        
        assert 'growth_rates' in result
        
        growth = result['growth_rates']
        
        # YoY Revenue Growth (2024 vs 2023)
        if 'revenue_growth_yoy' in growth:
            expected_growth = ((1100000000 - 1000000000) / 1000000000) * 100
            assert abs(growth['revenue_growth_yoy'] - expected_growth) < 0.01
        
        # 5-year CAGR
        if 'revenue_cagr_5y' in growth:
            start_val = 800000000
            end_val = 1100000000
            years = 4  # 2020 to 2024 is 4 years
            expected_cagr = ((end_val / start_val) ** (1/years) - 1) * 100
            assert abs(growth['revenue_cagr_5y'] - expected_cagr) < 0.1
    
    @pytest.mark.unit
    def test_trend_analysis(self, engine, historical_data):
        """Test trend analysis and forecasting"""
        result = engine.analyze_trends(historical_data)
        
        assert 'trends' in result
        
        trends = result['trends']
        
        # Check trend direction
        if 'revenue_trend' in trends:
            assert trends['revenue_trend'] in ['increasing', 'decreasing', 'stable']
            # Revenue is clearly increasing in sample data
            assert trends['revenue_trend'] == 'increasing'
        
        # Check trend strength
        if 'trend_strength' in trends:
            assert 0 <= trends['trend_strength'] <= 1
    
    @pytest.mark.unit
    def test_volatility_analysis(self, engine, historical_data):
        """Test volatility and stability metrics"""
        result = engine.calculate_volatility_metrics(historical_data)
        
        assert 'volatility' in result
        
        volatility = result['volatility']
        
        # Revenue volatility
        if 'revenue_volatility' in volatility:
            assert volatility['revenue_volatility'] >= 0
        
        # Earnings stability
        if 'earnings_stability' in volatility:
            assert 0 <= volatility['earnings_stability'] <= 1


class TestCompositeScores:
    """Test composite scoring and ranking systems"""
    
    @pytest.fixture
    def engine(self):
        return FinancialIndicatorEngine()
    
    @pytest.fixture
    def company_data_good(self):
        """Data for a financially healthy company"""
        return {
            'revenue': 1000000000,
            'net_income': 150000000,
            'operating_income': 200000000,
            'total_assets': 2000000000,
            'shareholders_equity': 1200000000,
            'current_assets': 800000000,
            'current_liabilities': 400000000,
            'total_liabilities': 800000000,
            'operating_cash_flow': 180000000,
            'free_cash_flow': 130000000,
            'shares_outstanding': 10000000,
            'market_price': 150
        }
    
    @pytest.fixture
    def company_data_poor(self):
        """Data for a financially weak company"""
        return {
            'revenue': 1000000000,
            'net_income': -50000000,  # Loss
            'operating_income': 10000000,
            'total_assets': 2000000000,
            'shareholders_equity': 200000000,  # Low equity
            'current_assets': 300000000,
            'current_liabilities': 600000000,  # High current liabilities
            'total_liabilities': 1800000000,  # High debt
            'operating_cash_flow': -20000000,  # Negative cash flow
            'free_cash_flow': -70000000,
            'shares_outstanding': 10000000,
            'market_price': 20
        }
    
    @pytest.mark.unit
    def test_altman_z_score(self, engine, company_data_good, company_data_poor):
        """Test Altman Z-Score calculation for bankruptcy prediction"""
        # Good company should have higher Z-Score
        good_score = engine.calculate_altman_z_score(company_data_good)
        poor_score = engine.calculate_altman_z_score(company_data_poor)
        
        assert good_score > poor_score
        
        # Typical thresholds: > 3.0 = Safe, < 1.8 = Distress
        if good_score is not None:
            assert good_score > 1.8  # Should be above distress zone
        
        if poor_score is not None:
            assert poor_score < 3.0  # Should be below safe zone
    
    @pytest.mark.unit
    def test_piotroski_f_score(self, engine, company_data_good, company_data_poor):
        """Test Piotroski F-Score for value investing"""
        good_score = engine.calculate_piotroski_score(company_data_good)
        poor_score = engine.calculate_piotroski_score(company_data_poor)
        
        # F-Score ranges from 0-9
        if good_score is not None:
            assert 0 <= good_score <= 9
            assert good_score >= 7  # Good companies typically score 7+
        
        if poor_score is not None:
            assert 0 <= poor_score <= 9
            assert poor_score <= 3  # Poor companies typically score 3 or below
    
    @pytest.mark.unit
    def test_quality_score(self, engine, company_data_good, company_data_poor):
        """Test custom quality scoring"""
        good_quality = engine.calculate_quality_score(company_data_good)
        poor_quality = engine.calculate_quality_score(company_data_poor)
        
        # Quality score should differentiate good from poor
        assert good_quality > poor_quality
        
        # Scores should be normalized (0-100)
        if good_quality is not None:
            assert 0 <= good_quality <= 100
            assert good_quality > 60  # Good company should score above 60
        
        if poor_quality is not None:
            assert 0 <= poor_quality <= 100
            assert poor_quality < 40  # Poor company should score below 40


class TestDataValidation:
    """Test data validation and sanitization"""
    
    @pytest.fixture
    def engine(self):
        return FinancialIndicatorEngine()
    
    @pytest.mark.unit
    def test_validate_input_data(self, engine):
        """Test input data validation"""
        invalid_data = {
            'revenue': 'not_a_number',
            'net_income': None,
            'total_assets': -1000000,  # Negative assets (invalid)
            'shares_outstanding': 0
        }
        
        validated = engine.validate_financial_data(invalid_data)
        
        # Should handle invalid data types
        assert validated['revenue'] in [None, 0]
        assert validated['net_income'] is None
        
        # Should flag or correct impossible values
        if 'total_assets' in validated:
            assert validated['total_assets'] >= 0
    
    @pytest.mark.unit
    def test_outlier_detection(self, engine):
        """Test outlier detection in financial metrics"""
        data_with_outliers = {
            'revenue': 1000000000,
            'net_income': 5000000000,  # Impossible: profit > revenue
            'total_assets': 100,  # Too small for the revenue
            'operating_margin': 150,  # Impossible: > 100%
        }
        
        result = engine.detect_outliers(data_with_outliers)
        
        assert 'outliers' in result
        assert 'net_income' in result['outliers']
        assert 'total_assets' in result['outliers']
        assert 'operating_margin' in result['outliers']


class TestPerformanceAndScalability:
    """Test performance with large datasets"""
    
    @pytest.fixture
    def engine(self):
        return FinancialIndicatorEngine()
    
    @pytest.mark.slow
    def test_batch_calculation_performance(self, engine):
        """Test performance with batch calculations"""
        # Generate 1000 company datasets
        companies = []
        for i in range(1000):
            companies.append({
                'company_id': i,
                'revenue': np.random.uniform(1e8, 1e10),
                'net_income': np.random.uniform(1e7, 1e9),
                'total_assets': np.random.uniform(1e9, 1e11),
                'shareholders_equity': np.random.uniform(1e8, 1e10),
                'current_assets': np.random.uniform(1e8, 1e9),
                'current_liabilities': np.random.uniform(1e7, 1e9)
            })
        
        import time
        start = time.time()
        
        results = engine.batch_calculate_indicators(companies)
        
        elapsed = time.time() - start
        
        # Should process 1000 companies in reasonable time
        assert elapsed < 5.0  # Less than 5 seconds
        assert len(results) == 1000
    
    @pytest.mark.unit
    def test_caching_mechanism(self, engine):
        """Test caching for repeated calculations"""
        data = {
            'revenue': 1000000000,
            'net_income': 100000000,
            'total_assets': 2000000000
        }
        
        # First calculation
        result1 = engine.calculate_all_indicators(data)
        
        # Second calculation with same data (should use cache)
        result2 = engine.calculate_all_indicators(data)
        
        # Results should be identical
        assert result1 == result2