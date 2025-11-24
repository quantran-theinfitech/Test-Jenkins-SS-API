"""Create index for subcriptions table

Revision ID: 7b46abe09f84
Revises: 84a7f48b5ba5
Create Date: 2023-07-27 04:03:02.374551

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "7b46abe09f84"
down_revision = "84a7f48b5ba5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_subcriptions_team_id", "subcriptions", ["team_id"], unique=False
    )
    op.create_index(
        "idx_subcriptions_service_code", "subcriptions", ["service_code"], unique=False
    )
    op.create_index(
        "idx_subcriptions_plan_code", "subcriptions", ["plan_code"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_subcriptions_plan_code", table_name="subcriptions")
    op.drop_index("idx_subcriptions_service_code", table_name="subcriptions")
    op.drop_index("idx_subcriptions_team_id", table_name="subcriptions")
