"""add intraday stock prices table

Revision ID: e2f0e6756928
Revises: 463ee6f38c6b
Create Date: 2025-11-16 15:59:45.436099

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e2f0e6756928"
down_revision: Union[str, None] = "463ee6f38c6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create intraday_stock_prices table
    op.create_table(
        "intraday_stock_prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("interval", sa.String(length=10), nullable=False),
        sa.Column("open_price", sa.Float(), nullable=True),
        sa.Column("high_price", sa.Float(), nullable=True),
        sa.Column("low_price", sa.Float(), nullable=True),
        sa.Column("close_price", sa.Float(), nullable=True),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("data_source", sa.String(length=50), server_default="yahoo_finance"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "timestamp", "interval", name="uq_intraday_company_time_interval"),
    )

    # Create indexes
    op.create_index(
        "idx_intraday_company_timestamp",
        "intraday_stock_prices",
        ["company_id", "timestamp"],
    )
    op.create_index(
        "idx_intraday_company_interval_timestamp",
        "intraday_stock_prices",
        ["company_id", "interval", "timestamp"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_intraday_company_interval_timestamp", table_name="intraday_stock_prices")
    op.drop_index("idx_intraday_company_timestamp", table_name="intraday_stock_prices")

    # Drop table
    op.drop_table("intraday_stock_prices")
