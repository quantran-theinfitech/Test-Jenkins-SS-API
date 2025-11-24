"""alter person_id table person_exclude_collection_items

Revision ID: 44edb1c7c388
Revises: 001a1544a338
Create Date: 2023-08-15 04:39:54.853110

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "44edb1c7c388"
down_revision = "001a1544a338"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "person_exclude_collection_items", "person_id", new_column_name="person_uuid"
    )
    op.alter_column(
        "person_exclude_collection_items", "person_uuid", type_=sa.String(length=64)
    )


def downgrade() -> None:
    op.alter_column(
        "person_exclude_collection_items", "person_uuid", new_column_name="person_id"
    )
    op.alter_column("person_exclude_collection_items", "person_id", type_=sa.Integer())
