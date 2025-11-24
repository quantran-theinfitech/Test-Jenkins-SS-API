"""Create index for company_collection_items table

Revision ID: 6d22236e8923
Revises: a4dae6920e09
Create Date: 2023-07-27 03:28:44.180731

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "6d22236e8923"
down_revision = "a4dae6920e09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_company_collection_items_hp_url",
        "company_collection_items",
        ["collection_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_company_collection_items_hp_url", table_name="company_collection_items"
    )
