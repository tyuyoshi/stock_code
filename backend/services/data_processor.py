"""Data Processing Service"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DataProcessor:
    """Service for processing financial data"""

    @staticmethod
    def calculate_financial_indicators(financial_data: Dict[str, float]) -> Dict[str, float]:
        """Calculate financial indicators from raw financial data"""
        indicators = {}
        
        try:
            # ROE (Return on Equity)
            if financial_data.get('net_income') and financial_data.get('shareholders_equity'):
                indicators['roe'] = (financial_data['net_income'] / financial_data['shareholders_equity']) * 100
            
            # ROA (Return on Assets)
            if financial_data.get('net_income') and financial_data.get('total_assets'):
                indicators['roa'] = (financial_data['net_income'] / financial_data['total_assets']) * 100
            
            # Current Ratio
            if financial_data.get('current_assets') and financial_data.get('current_liabilities'):
                indicators['current_ratio'] = financial_data['current_assets'] / financial_data['current_liabilities']
            
            # Debt to Equity
            if financial_data.get('total_liabilities') and financial_data.get('shareholders_equity'):
                indicators['debt_to_equity'] = financial_data['total_liabilities'] / financial_data['shareholders_equity']
            
            # Gross Margin
            if financial_data.get('gross_profit') and financial_data.get('revenue'):
                indicators['gross_margin'] = (financial_data['gross_profit'] / financial_data['revenue']) * 100
            
            # Operating Margin
            if financial_data.get('operating_income') and financial_data.get('revenue'):
                indicators['operating_margin'] = (financial_data['operating_income'] / financial_data['revenue']) * 100
            
            # Net Margin
            if financial_data.get('net_income') and financial_data.get('revenue'):
                indicators['net_margin'] = (financial_data['net_income'] / financial_data['revenue']) * 100
                
        except ZeroDivisionError as e:
            logger.error(f"Division by zero in financial calculations: {e}")
        except Exception as e:
            logger.error(f"Error calculating financial indicators: {e}")
        
        return indicators
    
    @staticmethod
    def calculate_market_indicators(
        stock_price: float,
        shares_outstanding: float,
        financial_data: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate market-based indicators"""
        indicators = {}
        
        try:
            market_cap = stock_price * shares_outstanding
            indicators['market_cap'] = market_cap
            
            # PER (Price to Earnings Ratio)
            if financial_data.get('net_income'):
                eps = financial_data['net_income'] / shares_outstanding
                indicators['per'] = stock_price / eps if eps > 0 else None
            
            # PBR (Price to Book Ratio)
            if financial_data.get('shareholders_equity'):
                bps = financial_data['shareholders_equity'] / shares_outstanding
                indicators['pbr'] = stock_price / bps if bps > 0 else None
            
            # PSR (Price to Sales Ratio)
            if financial_data.get('revenue'):
                indicators['psr'] = market_cap / financial_data['revenue']
                
        except Exception as e:
            logger.error(f"Error calculating market indicators: {e}")
        
        return indicators
    
    @staticmethod
    def clean_financial_data(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize financial data"""
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Handle missing values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        
        # Remove outliers (using IQR method)
        for col in numeric_columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            df[col] = df[col].clip(lower=lower, upper=upper)
        
        return df
    
    @staticmethod
    def calculate_growth_rates(current_data: Dict, previous_data: Dict) -> Dict[str, float]:
        """Calculate year-over-year growth rates"""
        growth_rates = {}
        
        metrics = ['revenue', 'net_income', 'operating_income']
        
        for metric in metrics:
            if metric in current_data and metric in previous_data:
                if previous_data[metric] != 0:
                    growth_rate = ((current_data[metric] - previous_data[metric]) / 
                                 abs(previous_data[metric])) * 100
                    growth_rates[f'{metric}_growth'] = growth_rate
        
        return growth_rates