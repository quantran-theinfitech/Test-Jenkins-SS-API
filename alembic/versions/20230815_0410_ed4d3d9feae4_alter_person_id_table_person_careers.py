"""alter person_id table person_careers

Revision ID: ed4d3d9feae4
Revises: cff4c8a79f16
Create Date: 2023-08-15 04:10:34.811930

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "ed4d3d9feae4"
down_revision = "cff4c8a79f16"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("person_careers", "person_id", new_column_name="person_uuid")
    op.alter_column("person_careers", "person_uuid", type_=sa.String(length=64))


def downgrade() -> None:
    op.alter_column("person_careers", "person_uuid", new_column_name="person_id")
    op.alter_column("person_careers", "person_id", type_=sa.Integer())
