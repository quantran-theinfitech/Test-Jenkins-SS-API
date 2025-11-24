"""Create index for company_collection table

Revision ID: a4dae6920e09
Revises: 634cc7252ce0
Create Date: 2023-07-27 03:24:57.538748

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a4dae6920e09"
down_revision = "634cc7252ce0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_company_collections_team_id",
        "company_collections",
        ["team_id"],
        unique=False,
    )
    op.create_index(
        "idx_company_collections_group_id",
        "company_collections",
        ["group_id"],
        unique=False,
    )
    op.create_index(
        "idx_company_collections_status_code",
        "company_collections",
        ["status_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_company_collections_status_code", table_name="company_collections"
    )
    op.drop_index("idx_company_collections_group_id", table_name="company_collections")
    op.drop_index("idx_company_collections_team_id", table_name="company_collections")
