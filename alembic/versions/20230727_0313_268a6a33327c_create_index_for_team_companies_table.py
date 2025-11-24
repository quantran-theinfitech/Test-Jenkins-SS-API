"""Create index for team_companies table

Revision ID: 268a6a33327c
Revises: 6e2bd693ecd4
Create Date: 2023-07-27 03:13:07.518232

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "268a6a33327c"
down_revision = "6e2bd693ecd4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_team_companies_corporate_number",
        "team_companies",
        ["corporate_number"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_team_companies_corporate_number", table_name="team_companies")
