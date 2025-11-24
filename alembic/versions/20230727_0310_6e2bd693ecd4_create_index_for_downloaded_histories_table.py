"""Create index for downloaded_histories table

Revision ID: 6e2bd693ecd4
Revises: 58a74f483831
Create Date: 2023-07-27 03:10:02.468063

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "6e2bd693ecd4"
down_revision = "58a74f483831"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_downloaded_histories_user_id",
        "downloaded_histories",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_downloaded_histories_user_id", table_name="downloaded_histories")
