"""Create index for activity_logs table

Revision ID: 522d7f3da67a
Revises: 7b46abe09f84
Create Date: 2023-07-27 04:04:58.166685

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "522d7f3da67a"
down_revision = "7b46abe09f84"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_activity_logs_corporate_number",
        "activity_logs",
        ["corporate_number"],
        unique=False,
    )
    op.create_index(
        "idx_activity_logs_model_id", "activity_logs", ["model_id"], unique=False
    )
    op.create_index(
        "idx_activity_logs_team_id", "activity_logs", ["team_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_activity_logs_team_id", table_name="activity_logs")
    op.drop_index("idx_activity_logs_model_id", table_name="activity_logs")
    op.drop_index("idx_activity_logs_corporate_number", table_name="activity_logs")
