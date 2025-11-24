"""alter company add normalized_name

Revision ID: 9b9831b1ef75
Revises: 90f5e9c1cd85
Create Date: 2025-02-06 16:16:05.547656

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "9b9831b1ef75"
down_revision = "90f5e9c1cd85"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("normalized_name", sa.Text(), nullable=True))
    op.create_index(
        op.f("ix_companies_normalized_name"),
        "companies",
        ["normalized_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_companies_normalized_name"), table_name="companies")
    op.drop_column("companies", "normalized_name")
