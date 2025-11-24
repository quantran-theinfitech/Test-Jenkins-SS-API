"""add form retry_count

Revision ID: 93f046873877
Revises: b9cf7c9389f7
Create Date: 2025-11-06 11:41:00.144171
"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "93f046873877"
down_revision = "b9cf7c9389f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "form_job_items",
        sa.Column("retry_count", sa.Integer(), nullable=True, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("form_job_items", "retry_count")
