"""add ingest_id to recruit table

Revision ID: 8180617f6f7e
Revises: 07167d5c522a
Create Date: 2023-10-19 08:58:34.322029

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8180617f6f7e"
down_revision = "07167d5c522a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "recruits", sa.Column("ingest_id", sa.String(length=64), nullable=True)
    )
    op.create_index("idx_recruits_ingest_id", "recruits", ["ingest_id"])


def downgrade() -> None:
    op.drop_index("idx_recruits_ingest_id")
    op.drop_column("recruits", "ingest_id")
