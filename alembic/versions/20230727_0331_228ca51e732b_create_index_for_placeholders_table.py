"""Create index for placeholders table

Revision ID: 228ca51e732b
Revises: 108194feb749
Create Date: 2023-07-27 03:31:46.438524

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "228ca51e732b"
down_revision = "108194feb749"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_placeholders_created_at", "placeholders", ["created_at"], unique=False
    )
    op.create_index(
        "idx_placeholders_team_id", "placeholders", ["team_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_placeholders_team_id", table_name="placeholders")
    op.drop_index("idx_placeholders_created_at", table_name="placeholders")
