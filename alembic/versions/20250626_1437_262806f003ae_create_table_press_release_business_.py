"""create table press_release_business_categories

Revision ID: 262806f003ae
Revises: c9957eb6d58f
Create Date: 2025-06-26 14:37:48.864139

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "262806f003ae"
down_revision = "c9957eb6d58f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "press_release_business_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=True
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=True
        ),
    )


def downgrade() -> None:
    op.drop_table("press_release_business_categories")
