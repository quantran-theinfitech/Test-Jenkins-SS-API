"""Create index for users table

Revision ID: 58a74f483831
Revises: abdcc7ea3bcf
Create Date: 2023-07-27 03:07:49.535425

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "58a74f483831"
down_revision = "abdcc7ea3bcf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("idx_users_team_id", "users", ["team_id"], unique=False)
    op.create_index("idx_users_role_code", "users", ["role_code"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_users_role_code", table_name="users")
    op.drop_index("idx_users_team_id", table_name="users")
