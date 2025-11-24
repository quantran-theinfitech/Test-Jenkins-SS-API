"""alter person_id table team_persons

Revision ID: e08e848c5465
Revises: 5c57a5857783
Create Date: 2023-08-15 04:41:43.930318

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e08e848c5465"
down_revision = "5c57a5857783"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("team_persons", "person_id", new_column_name="person_uuid")
    op.alter_column("team_persons", "person_uuid", type_=sa.String(length=64))


def downgrade() -> None:
    op.alter_column("team_persons", "person_uuid", new_column_name="person_id")
    op.alter_column("team_persons", "person_id", type_=sa.Integer())
