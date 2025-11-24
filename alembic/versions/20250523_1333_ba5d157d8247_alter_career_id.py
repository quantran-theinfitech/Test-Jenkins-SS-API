"""alter career_id

Revision ID: ba5d157d8247
Revises: 1b55c52dad7f
Create Date: 2025-05-23 13:33:56.032719

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "ba5d157d8247"
down_revision = "1b55c52dad7f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "person_careers",
        "career_id",
        existing_type=sa.VARCHAR(length=255),
        type_=sa.String(length=500),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "person_careers",
        "career_id",
        existing_type=sa.String(length=500),
        type_=sa.VARCHAR(length=255),
        existing_nullable=True,
    )
