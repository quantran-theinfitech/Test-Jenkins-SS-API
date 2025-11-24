"""Updated index team_companies table

Revision ID: 6355f4849f24
Revises: ba51a9b29821
Create Date: 2023-07-18 02:56:08.986976

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "6355f4849f24"
down_revision = "ba51a9b29821"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("idx_team_companies_team_id", "team_companies", ["team_id"])


def downgrade() -> None:
    op.drop_index("idx_team_companies_team_id")
