"""add tool
Revision ID: c31eb228974c
Revises: fccd109aee98
Create Date: 2025-04-28 10:38:39.606289
"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "c31eb228974c"
down_revision = "fccd109aee98"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add a 'tool' column to an existing table
    # Note: You need to specify which table to add it to
    op.add_column("events", sa.Column("tool", sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remove the 'tool' column
    op.drop_column("events", "tool")
