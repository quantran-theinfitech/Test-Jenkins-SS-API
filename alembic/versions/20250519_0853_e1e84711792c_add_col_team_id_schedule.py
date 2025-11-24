"""add col team_id schedule

Revision ID: e1e84711792c
Revises: e93d5fa5661b
Create Date: 2025-05-19 08:53:58.582477

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e1e84711792c"
down_revision = "e93d5fa5661b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sequence_campaign_schedules", sa.Column("team_id", sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("sequence_campaign_schedules", "team_id")
