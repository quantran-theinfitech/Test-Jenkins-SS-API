"""add col show_tutorial_flag table users

Revision ID: decb0c741bad
Revises: 9fb2fa4910ae
Create Date: 2025-06-17 14:26:46.024652

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "decb0c741bad"
down_revision = "9fb2fa4910ae"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("show_tutorial_flag", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "show_tutorial_flag")
