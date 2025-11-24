"""add s3_object_key column in enrichment_files table

Revision ID: 4a1b9c912cfe
Revises: 915558bda20d
Create Date: 2025-11-11 08:21:41.229034

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "4a1b9c912cfe"
down_revision = "915558bda20d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "enrichment_files",
        sa.Column("s3_object_key", sa.String(length=255), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_column("enrichment_files", "s3_object_key")
    # ### end Alembic commands ###
