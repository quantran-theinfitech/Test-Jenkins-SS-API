"""Create index for teams table

Revision ID: e82f3403147d
Revises: a98a9bc15834
Create Date: 2023-07-27 04:00:22.510565

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "e82f3403147d"
down_revision = "a98a9bc15834"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_teams_form_plan_code", "teams", ["form_plan_code"], unique=False
    )
    op.create_index(
        "idx_teams_listing_plan_code", "teams", ["listing_plan_code"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_teams_listing_plan_code", table_name="teams")
    op.drop_index("idx_teams_form_plan_code", table_name="teams")
