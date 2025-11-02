"""
SQLAlchemy Models Package

This module aggregates all database models for Alembic migration system.
Import all models here to ensure they are registered with SQLAlchemy's Base metadata.
"""

from core.database import Base
from models.company import Company
from models.financial import FinancialStatement, StockPrice, FinancialIndicator

# Export all models and Base for Alembic
__all__ = [
    'Base',
    'Company',
    'FinancialStatement',
    'StockPrice',
    'FinancialIndicator',
]

# This ensures all models are loaded when importing from models
# Required for Alembic autogenerate to detect all tables