"""update hubspot company sync histories table

Revision ID: 20dce537fad0
Revises: f3358786e7bf
Create Date: 2025-01-14 10:47:11.814451

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20dce537fad0"
down_revision = "f3358786e7bf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "hubspot_company_sync_histories",
        sa.Column("hubspot_push_type", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("hubspot_company_sync_histories", "hubspot_push_type")
