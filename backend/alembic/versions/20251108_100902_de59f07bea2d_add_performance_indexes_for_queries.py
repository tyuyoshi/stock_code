"""Add performance indexes for queries

Revision ID: de59f07bea2d
Revises: 0607ff91625c
Create Date: 2025-11-08 10:09:02.817844

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "de59f07bea2d"
down_revision: Union[str, None] = "0607ff91625c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Financial indicators indexes for common queries
    op.create_index(
        "idx_financial_indicator_company_date",
        "financial_indicators",
        ["company_id", sa.text("date DESC")],
    )
    op.create_index("idx_financial_indicator_roe", "financial_indicators", ["roe"])
    op.create_index("idx_financial_indicator_per", "financial_indicators", ["per"])
    op.create_index("idx_financial_indicator_pbr", "financial_indicators", ["pbr"])

    # Companies indexes for filtering
    op.create_index("idx_companies_market_division", "companies", ["market_division"])
    op.create_index("idx_companies_industry_code", "companies", ["industry_code"])

    # Stock prices index for date-based queries
    op.create_index(
        "idx_stock_prices_company_date",
        "stock_prices",
        ["company_id", sa.text("date DESC")],
    )


def downgrade() -> None:
    # Drop indexes in reverse order
    op.drop_index("idx_stock_prices_company_date", "stock_prices")
    op.drop_index("idx_companies_industry_code", "companies")
    op.drop_index("idx_companies_market_division", "companies")
    op.drop_index("idx_financial_indicator_pbr", "financial_indicators")
    op.drop_index("idx_financial_indicator_per", "financial_indicators")
    op.drop_index("idx_financial_indicator_roe", "financial_indicators")
    op.drop_index("idx_financial_indicator_company_date", "financial_indicators")
