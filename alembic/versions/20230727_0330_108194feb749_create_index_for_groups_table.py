"""Create index for groups table

Revision ID: 108194feb749
Revises: 1fe257710cdc
Create Date: 2023-07-27 03:30:45.022387

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "108194feb749"
down_revision = "1fe257710cdc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("idx_groups_team_id", "groups", ["team_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_groups_team_id", table_name="groups")
