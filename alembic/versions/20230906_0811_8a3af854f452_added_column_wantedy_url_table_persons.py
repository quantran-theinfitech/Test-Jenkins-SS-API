"""Added column wantedy_url table persons

Revision ID: 8a3af854f452
Revises: 58267e1267a7
Create Date: 2023-09-06 08:11:32.536434

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8a3af854f452"
down_revision = "58267e1267a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "persons",
        sa.Column("wantedly_url", sa.String(length=1024), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("persons", "wantedly_url")
