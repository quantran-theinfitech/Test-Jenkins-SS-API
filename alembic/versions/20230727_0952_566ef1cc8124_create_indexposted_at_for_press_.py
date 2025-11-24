"""Create indexposted_at for press_releases table

Revision ID: 566ef1cc8124
Revises: efe96cb15a7a
Create Date: 2023-07-27 09:52:55.771376

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "566ef1cc8124"
down_revision = "efe96cb15a7a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_press_releases_posted_at", "press_releases", ["posted_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_press_releases_posted_at", table_name="press_releases")
