"""
Tests for Data Processor
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from services.data_processor import DataProcessor


class TestDataProcessor:
    """Test suite for Data Processor"""
    
    @pytest.fixture
    def processor(self):
        """Create DataProcessor instance"""
        return DataProcessor()
    
    @pytest.fixture
    def sample_financial_data(self):
        """Sample financial data for testing"""
        return {
            "revenue": 1000000000,
            "operating_income": 150000000,
            "net_income": 100000000,
            "total_assets": 2000000000,
            "current_assets": 800000000,
            "total_liabilities": 1200000000,
            "current_liabilities": 400000000,
            "shareholders_equity": 800000000,
            "cash_flow_operating": 120000000,
            "cash_flow_investing": -50000000,
            "cash_flow_financing": -30000000,
            "shares_outstanding": 10000000
        }
    
    @pytest.fixture
    def sample_market_data(self):
        """Sample market data for testing"""
        return {
            "current_price": 2500,
            "previous_close": 2450,
            "high_52week": 3000,
            "low_52week": 2000,
            "volume": 1000000,
            "average_volume": 800000,
            "market_cap": 25000000000,
            "beta": 1.2
        }
    
    @pytest.fixture
    def sample_dataframe(self):
        """Sample DataFrame with historical financial data"""
        dates = pd.date_range(end=datetime.now(), periods=4, freq='Y')
        return pd.DataFrame({
            "fiscal_year": [2021, 2022, 2023, 2024],
            "revenue": [800000000, 900000000, 950000000, 1000000000],
            "net_income": [50000000, 70000000, 85000000, 100000000],
            "total_assets": [1500000000, 1700000000, 1850000000, 2000000000],
            "shareholders_equity": [600000000, 700000000, 750000000, 800000000],
            "eps": [5.0, 7.0, 8.5, 10.0],
            "dividend_per_share": [1.0, 1.2, 1.4, 1.5]
        })
    
    @pytest.mark.unit
    def test_calculate_financial_indicators(self, processor, sample_financial_data):
        """Test calculation of financial indicators"""
        result = processor.calculate_financial_indicators(sample_financial_data)
        
        assert "profitability" in result
        assert "efficiency" in result
        assert "liquidity" in result
        assert "leverage" in result
        
        # Test profitability indicators
        profitability = result["profitability"]
        assert "roe" in profitability  # Return on Equity
        assert "roa" in profitability  # Return on Assets
        assert "operating_margin" in profitability
        assert "net_margin" in profitability
        
        # Verify calculations
        expected_roe = (100000000 / 800000000) * 100  # 12.5%
        expected_roa = (100000000 / 2000000000) * 100  # 5%
        expected_operating_margin = (150000000 / 1000000000) * 100  # 15%
        expected_net_margin = (100000000 / 1000000000) * 100  # 10%
        
        assert abs(profitability["roe"] - expected_roe) < 0.01
        assert abs(profitability["roa"] - expected_roa) < 0.01
        assert abs(profitability["operating_margin"] - expected_operating_margin) < 0.01
        assert abs(profitability["net_margin"] - expected_net_margin) < 0.01
        
        # Test liquidity indicators
        liquidity = result["liquidity"]
        assert "current_ratio" in liquidity
        assert "quick_ratio" in liquidity
        
        expected_current_ratio = 800000000 / 400000000  # 2.0
        assert abs(liquidity["current_ratio"] - expected_current_ratio) < 0.01
        
        # Test leverage indicators
        leverage = result["leverage"]
        assert "debt_to_equity" in leverage
        assert "equity_ratio" in leverage
        
        expected_debt_to_equity = 1200000000 / 800000000  # 1.5
        expected_equity_ratio = (800000000 / 2000000000) * 100  # 40%
        
        assert abs(leverage["debt_to_equity"] - expected_debt_to_equity) < 0.01
        assert abs(leverage["equity_ratio"] - expected_equity_ratio) < 0.01
    
    @pytest.mark.unit
    def test_calculate_financial_indicators_missing_data(self, processor):
        """Test calculation with missing data"""
        incomplete_data = {
            "revenue": 1000000000,
            "net_income": 100000000,
            # Missing other fields
        }
        
        result = processor.calculate_financial_indicators(incomplete_data)
        
        # Should handle missing data gracefully
        assert result is not None
        assert "profitability" in result
        
        # Indicators requiring missing data should be None or 0
        if "roe" in result["profitability"]:
            assert result["profitability"]["roe"] in [None, 0]
    
    @pytest.mark.unit
    def test_calculate_financial_indicators_zero_values(self, processor):
        """Test calculation with zero values to avoid division by zero"""
        zero_data = {
            "revenue": 0,
            "net_income": 100000000,
            "total_assets": 2000000000,
            "shareholders_equity": 0,
            "current_assets": 800000000,
            "current_liabilities": 0,
            "total_liabilities": 1200000000
        }
        
        result = processor.calculate_financial_indicators(zero_data)
        
        # Should handle division by zero
        assert result is not None
        
        # ROE should be None or inf when shareholders_equity is 0
        profitability = result.get("profitability", {})
        if "roe" in profitability:
            assert profitability["roe"] in [None, float('inf'), 0]
        
        # Current ratio should be None or inf when current_liabilities is 0
        liquidity = result.get("liquidity", {})
        if "current_ratio" in liquidity:
            assert liquidity["current_ratio"] in [None, float('inf'), 0]
    
    @pytest.mark.unit
    def test_calculate_market_indicators(self, processor, sample_market_data, sample_financial_data):
        """Test calculation of market indicators"""
        result = processor.calculate_market_indicators(
            sample_market_data, 
            sample_financial_data
        )
        
        assert "valuation" in result
        assert "price_metrics" in result
        assert "volume_metrics" in result
        
        # Test valuation metrics
        valuation = result["valuation"]
        assert "per" in valuation  # P/E Ratio
        assert "pbr" in valuation  # P/B Ratio
        assert "psr" in valuation  # P/S Ratio
        assert "dividend_yield" in valuation
        
        # Verify P/E calculation
        eps = sample_financial_data["net_income"] / sample_financial_data["shares_outstanding"]
        expected_per = sample_market_data["current_price"] / eps
        
        if "per" in valuation and valuation["per"] is not None:
            assert abs(valuation["per"] - expected_per) < 0.1
        
        # Test price metrics
        price_metrics = result["price_metrics"]
        assert "price_change" in price_metrics
        assert "price_change_percent" in price_metrics
        assert "52week_range_position" in price_metrics
        
        # Verify price change calculation
        expected_change = sample_market_data["current_price"] - sample_market_data["previous_close"]
        expected_change_percent = (expected_change / sample_market_data["previous_close"]) * 100
        
        assert abs(price_metrics["price_change"] - expected_change) < 0.01
        assert abs(price_metrics["price_change_percent"] - expected_change_percent) < 0.01
        
        # Test volume metrics
        volume_metrics = result["volume_metrics"]
        assert "volume_ratio" in volume_metrics
        
        expected_volume_ratio = sample_market_data["volume"] / sample_market_data["average_volume"]
        assert abs(volume_metrics["volume_ratio"] - expected_volume_ratio) < 0.01
    
    @pytest.mark.unit
    def test_clean_financial_data(self, processor):
        """Test data cleaning functionality"""
        dirty_data = {
            "revenue": "1,000,000,000",
            "net_income": "100000000",
            "invalid_field": "N/A",
            "empty_field": "",
            "null_field": None,
            "negative_value": "-50000",
            "percentage": "15.5%",
            "with_currency": "¥1000000"
        }
        
        result = processor.clean_financial_data(dirty_data)
        
        # Check that strings are converted to numbers
        assert result["revenue"] == 1000000000
        assert result["net_income"] == 100000000
        assert result["negative_value"] == -50000
        
        # Check that invalid values are handled
        assert result.get("invalid_field") in [None, 0, "N/A"]
        assert result.get("empty_field") in [None, 0, ""]
        assert result.get("null_field") is None
        
        # Check that percentages and currency symbols are handled
        if "percentage" in result and isinstance(result["percentage"], (int, float)):
            assert abs(result["percentage"] - 15.5) < 0.01 or abs(result["percentage"] - 0.155) < 0.001
    
    @pytest.mark.unit
    def test_clean_financial_data_dataframe(self, processor, sample_dataframe):
        """Test cleaning of DataFrame data"""
        # Add some dirty data to the DataFrame
        dirty_df = sample_dataframe.copy()
        dirty_df.loc[0, "revenue"] = "800,000,000"
        dirty_df.loc[1, "net_income"] = np.nan
        dirty_df.loc[2, "total_assets"] = "N/A"
        
        result = processor.clean_financial_data(dirty_df)
        
        # Check that it returns a DataFrame
        assert isinstance(result, pd.DataFrame)
        
        # Check that string values are converted
        assert result.loc[0, "revenue"] == 800000000
        
        # Check that NaN values are handled (usually filled with 0 or kept as NaN)
        assert pd.isna(result.loc[1, "net_income"]) or result.loc[1, "net_income"] == 0
    
    @pytest.mark.unit
    def test_calculate_growth_rates(self, processor, sample_dataframe):
        """Test growth rate calculations"""
        result = processor.calculate_growth_rates(sample_dataframe)
        
        assert "revenue_growth" in result
        assert "net_income_growth" in result
        assert "eps_growth" in result
        
        # Test YoY growth rates
        if "yoy" in result:
            yoy = result["yoy"]
            
            # Latest year revenue growth: (1000000000 - 950000000) / 950000000
            expected_revenue_growth = ((1000000000 - 950000000) / 950000000) * 100
            
            if "revenue_growth" in yoy:
                assert abs(yoy["revenue_growth"] - expected_revenue_growth) < 0.1
        
        # Test CAGR (Compound Annual Growth Rate)
        if "cagr" in result:
            cagr = result["cagr"]
            
            # 3-year CAGR for revenue
            years = 3
            start_revenue = 800000000
            end_revenue = 1000000000
            expected_cagr = ((end_revenue / start_revenue) ** (1/years) - 1) * 100
            
            if "revenue_cagr_3y" in cagr:
                assert abs(cagr["revenue_cagr_3y"] - expected_cagr) < 0.5
    
    @pytest.mark.unit
    def test_calculate_growth_rates_insufficient_data(self, processor):
        """Test growth rate calculation with insufficient data"""
        # DataFrame with only one row
        single_row_df = pd.DataFrame({
            "fiscal_year": [2024],
            "revenue": [1000000000],
            "net_income": [100000000]
        })
        
        result = processor.calculate_growth_rates(single_row_df)
        
        # Should handle single row gracefully
        assert result is not None
        
        # Growth rates should be None or 0 with insufficient data
        if "yoy" in result:
            for key, value in result["yoy"].items():
                assert value in [None, 0]
    
    @pytest.mark.integration
    def test_full_data_processing_pipeline(self, processor, sample_financial_data, sample_market_data):
        """Test complete data processing pipeline"""
        # Step 1: Clean financial data
        cleaned_data = processor.clean_financial_data(sample_financial_data)
        assert cleaned_data is not None
        
        # Step 2: Calculate financial indicators
        financial_indicators = processor.calculate_financial_indicators(cleaned_data)
        assert financial_indicators is not None
        assert len(financial_indicators) > 0
        
        # Step 3: Calculate market indicators
        market_indicators = processor.calculate_market_indicators(
            sample_market_data,
            cleaned_data
        )
        assert market_indicators is not None
        assert len(market_indicators) > 0
        
        # Step 4: Combine results
        combined_result = {
            **financial_indicators,
            **market_indicators
        }
        
        # Verify combined result has all expected categories
        expected_categories = ["profitability", "efficiency", "liquidity", 
                             "leverage", "valuation", "price_metrics"]
        
        for category in expected_categories:
            assert category in combined_result
    
    @pytest.mark.unit
    def test_handle_negative_values(self, processor):
        """Test handling of negative values (e.g., losses, negative cash flow)"""
        negative_data = {
            "revenue": 1000000000,
            "net_income": -50000000,  # Loss
            "cash_flow_operating": -20000000,  # Negative operating cash flow
            "cash_flow_investing": -100000000,
            "cash_flow_financing": 150000000,
            "total_assets": 2000000000,
            "shareholders_equity": 800000000
        }
        
        result = processor.calculate_financial_indicators(negative_data)
        
        # Should handle negative values properly
        assert result is not None
        
        # ROE should be negative when net_income is negative
        if "roe" in result.get("profitability", {}):
            assert result["profitability"]["roe"] < 0
        
        # Net margin should be negative
        if "net_margin" in result.get("profitability", {}):
            assert result["profitability"]["net_margin"] < 0


class TestDataProcessorPerformance:
    """Performance tests for Data Processor"""
    
    @pytest.mark.slow
    def test_large_dataframe_processing(self):
        """Test processing of large DataFrame"""
        processor = DataProcessor()
        
        # Create large DataFrame with 10 years of quarterly data
        dates = pd.date_range(end=datetime.now(), periods=40, freq='Q')
        large_df = pd.DataFrame({
            "date": dates,
            "revenue": np.random.uniform(900000000, 1100000000, 40),
            "net_income": np.random.uniform(80000000, 120000000, 40),
            "total_assets": np.random.uniform(1800000000, 2200000000, 40),
            "shareholders_equity": np.random.uniform(700000000, 900000000, 40),
            "eps": np.random.uniform(8, 12, 40),
            "dividend_per_share": np.random.uniform(1, 2, 40)
        })
        
        # Should process large DataFrame efficiently
        start_time = datetime.now()
        result = processor.calculate_growth_rates(large_df)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        assert result is not None
        assert processing_time < 1.0  # Should process in less than 1 second