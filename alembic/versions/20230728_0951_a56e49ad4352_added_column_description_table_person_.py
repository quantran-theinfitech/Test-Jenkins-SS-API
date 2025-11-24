"""Added column description table person_exclude_collections

Revision ID: a56e49ad4352
Revises: ac42fda3948e
Create Date: 2023-07-28 09:51:12.592701

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a56e49ad4352"
down_revision = "ac42fda3948e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "person_exclude_collections",
        sa.Column("description", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("person_exclude_collections", "description")
