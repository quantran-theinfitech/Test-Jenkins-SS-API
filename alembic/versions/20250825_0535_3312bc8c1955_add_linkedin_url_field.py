"""add linkedin_url field

Revision ID: 3312bc8c1955
Revises: 7aab9abcd21f
Create Date: 2025-08-25 05:35:41.760559

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "3312bc8c1955"
down_revision = "7aab9abcd21f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("linkedin_url", sa.TEXT(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("companies", "linkedin_url")
