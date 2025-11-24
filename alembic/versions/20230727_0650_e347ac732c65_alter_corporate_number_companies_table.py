"""alter_corporate_number_companies_table

Revision ID: e347ac732c65
Revises: efe96cb15a7a
Create Date: 2023-07-27 06:50:24.984406

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e347ac732c65"
down_revision = "efe96cb15a7a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("companies", "corporate_number", type_=sa.String(length=64))


def downgrade() -> None:
    op.alter_column("companies", "corporate_number", type_=sa.TEXT())
