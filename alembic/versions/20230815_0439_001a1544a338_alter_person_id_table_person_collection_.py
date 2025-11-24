"""alter person_id table person_collection_items

Revision ID: 001a1544a338
Revises: b0116a927119
Create Date: 2023-08-15 04:39:09.082475

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "001a1544a338"
down_revision = "b0116a927119"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "person_collection_items", "person_id", new_column_name="person_uuid"
    )
    op.alter_column(
        "person_collection_items", "person_uuid", type_=sa.String(length=64)
    )


def downgrade() -> None:
    op.alter_column(
        "person_collection_items", "person_uuid", new_column_name="person_id"
    )
    op.alter_column("person_collection_items", "person_id", type_=sa.Integer())
