"""alter_corporate_number_todos_table

Revision ID: e709f99b4e1d
Revises: dd27b2e607ff
Create Date: 2023-07-27 07:03:58.797652

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e709f99b4e1d"
down_revision = "dd27b2e607ff"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("todos", "corporate_number", type_=sa.String(length=64))


def downgrade() -> None:
    op.alter_column("todos", "corporate_number", type_=sa.TEXT())
