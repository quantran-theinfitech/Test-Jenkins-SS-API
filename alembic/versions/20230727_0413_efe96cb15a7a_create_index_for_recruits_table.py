"""Create index for recruits table

Revision ID: efe96cb15a7a
Revises: 522d7f3da67a
Create Date: 2023-07-27 04:13:46.048898

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "efe96cb15a7a"
down_revision = "522d7f3da67a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_recruits_corporate_number", "recruits", ["corporate_number"], unique=False
    )
    op.create_index("idx_recruits_created_at", "recruits", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_recruits_created_at", table_name="recruits")
    op.drop_index("idx_recruits_corporate_number", table_name="recruits")
