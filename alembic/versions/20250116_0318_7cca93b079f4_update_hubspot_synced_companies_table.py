"""update hubspot synced companies table

Revision ID: 7cca93b079f4
Revises: 20dce537fad0
Create Date: 2025-01-16 03:18:42.303172

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "7cca93b079f4"
down_revision = "20dce537fad0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("hubspot_synced_companies", "hubspot_company_id")
    op.add_column(
        "hubspot_synced_companies",
        sa.Column("hubspot_company_id", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("hubspot_synced_companies", "hubspot_company_id")
    op.add_column(
        "hubspot_synced_companies",
        sa.Column("hubspot_company_id", sa.Integer(), nullable=True),
    )
