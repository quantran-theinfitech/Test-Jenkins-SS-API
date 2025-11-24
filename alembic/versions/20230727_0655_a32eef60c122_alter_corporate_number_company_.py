"""alter_corporate_number_company_collection_items_table

Revision ID: a32eef60c122
Revises: e347ac732c65
Create Date: 2023-07-27 06:55:08.337747

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a32eef60c122"
down_revision = "e347ac732c65"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "company_collection_items", "corporate_number", type_=sa.String(length=64)
    )


def downgrade() -> None:
    op.alter_column("company_collection_items", "corporate_number", type_=sa.TEXT())
