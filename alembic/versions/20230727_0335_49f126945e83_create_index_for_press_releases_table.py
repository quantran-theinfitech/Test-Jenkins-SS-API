"""Create index for press_releases table

Revision ID: 49f126945e83
Revises: 1e677f6e1d69
Create Date: 2023-07-27 03:35:19.828499

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "49f126945e83"
down_revision = "1e677f6e1d69"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_press_releases_created_at", "press_releases", ["created_at"], unique=False
    )
    op.create_index(
        "idx_press_releases_corporate_number",
        "press_releases",
        ["corporate_number"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_press_releases_corporate_number", table_name="press_releases")
    op.drop_index("idx_press_releases_created_at", table_name="press_releases")
