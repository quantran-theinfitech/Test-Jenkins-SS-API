"""alter person_id table person_bookmarks

Revision ID: b0116a927119
Revises: 0295c38931b7
Create Date: 2023-08-15 04:38:35.235597

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "b0116a927119"
down_revision = "0295c38931b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("person_bookmarks", "person_id", new_column_name="person_uuid")
    op.alter_column("person_bookmarks", "person_uuid", type_=sa.String(length=64))


def downgrade() -> None:
    op.alter_column("person_bookmarks", "person_uuid", new_column_name="person_id")
    op.alter_column("person_bookmarks", "person_id", type_=sa.Integer())
