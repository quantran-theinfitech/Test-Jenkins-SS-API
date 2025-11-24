"""alter_corporate_number_activity_logs_table

Revision ID: dd27b2e607ff
Revises: 5216902b4c79
Create Date: 2023-07-27 07:03:39.027236

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "dd27b2e607ff"
down_revision = "5216902b4c79"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("activity_logs", "corporate_number", type_=sa.String(length=64))


def downgrade() -> None:
    op.alter_column("activity_logs", "corporate_number", type_=sa.TEXT())
