"""Create index for companies table

Revision ID: 634cc7252ce0
Revises: 268a6a33327c
Create Date: 2023-07-27 03:16:32.787114

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "634cc7252ce0"
down_revision = "268a6a33327c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("idx_companies_hp_url", "companies", ["hp_url"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_companies_hp_url", table_name="companies")
