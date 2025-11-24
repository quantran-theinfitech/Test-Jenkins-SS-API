"""add col status enrich items

Revision ID: 373aa271b60a
Revises: 03a370ae3107
Create Date: 2025-07-07 14:22:20.101346

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "373aa271b60a"
down_revision = "46ae6a64fc50"
branch_labels = None
depends_on = None


def upgrade() -> None:
    enrichment_status = postgresql.ENUM(
        "BEING_IDENTIFIED", "IDENTIFIED", "FAILED", name="enrichment_item_status"
    )
    enrichment_status.create(op.get_bind())
    op.add_column(
        "enrichment_items",
        sa.Column(
            "status",
            sa.Enum(
                "BEING_IDENTIFIED",
                "IDENTIFIED",
                "FAILED",
                name="enrichment_item_status",
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("enrichment_items", "status")
    enrichment_status = postgresql.ENUM(
        "BEING_IDENTIFIED", "IDENTIFIED", "FAILED", name="enrichment_item_status"
    )
    enrichment_status.drop(op.get_bind())
