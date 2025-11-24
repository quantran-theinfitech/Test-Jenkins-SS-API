"""create index for team_credits table

Revision ID: c536df5df400
Revises: 0d8ff2f140dc
Create Date: 2023-07-27 02:40:33.342485

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c536df5df400"
down_revision = "0d8ff2f140dc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_team_credits_service_code", "team_credits", ["service_code"], unique=False
    )
    op.create_index(
        "idx_team_credits_team_id", "team_credits", ["team_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_team_credits_service_code", table_name="team_credits")
    op.drop_index("idx_team_credits_team_id", table_name="team_credits")
