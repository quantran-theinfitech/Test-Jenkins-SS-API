"""create column revenue_ai_score

Revision ID: 7aab9abcd21f
Revises: 9e899141d420
Create Date: 2025-08-06 11:01:51.733786

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "7aab9abcd21f"
down_revision = "9e899141d420"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("revenue_ai_score", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("companies", "revenue_ai_score")
