"""empty message

Revision ID: 9e899141d420
Revises: c31eb228974c
Create Date: 2025-05-07 15:40:55.418368

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9e899141d420"
down_revision = "c31eb228974c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("revenue_ai", sa.BigInteger(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("companies", "revenue_ai")
