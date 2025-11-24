"""Create index for placeholder_items table

Revision ID: 1e677f6e1d69
Revises: 228ca51e732b
Create Date: 2023-07-27 03:34:22.095317

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "1e677f6e1d69"
down_revision = "228ca51e732b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_placeholder_items_placeholder_id",
        "placeholder_items",
        ["placeholder_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_placeholder_items_placeholder_id", table_name="placeholder_items"
    )
