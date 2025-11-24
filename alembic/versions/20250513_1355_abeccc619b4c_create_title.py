"""create_title

Revision ID: abeccc619b4c
Revises: de9cfc6c7ae9
Create Date: 2025-05-13 13:55:39.222446

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "abeccc619b4c"
down_revision = "de9cfc6c7ae9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("company_services", sa.Column("title", sa.TEXT(), nullable=True))


def downgrade() -> None:
    op.drop_column("company_services", "title")
