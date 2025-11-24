"""Create index for plans table

Revision ID: 84a7f48b5ba5
Revises: e82f3403147d
Create Date: 2023-07-27 04:01:13.827359

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "84a7f48b5ba5"
down_revision = "e82f3403147d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("idx_plans_service_code", "plans", ["service_code"], unique=False)
    op.create_index("idx_plans_name_code", "plans", ["name_code"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_plans_name_code", table_name="plans")
    op.drop_index("idx_plans_service_code", table_name="plans")
