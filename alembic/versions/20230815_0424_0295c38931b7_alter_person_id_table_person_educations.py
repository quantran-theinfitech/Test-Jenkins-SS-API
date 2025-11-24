"""alter person_id table person_educations

Revision ID: 0295c38931b7
Revises: ed4d3d9feae4
Create Date: 2023-08-15 04:24:16.184923

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0295c38931b7"
down_revision = "ed4d3d9feae4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("person_educations", "person_id", new_column_name="person_uuid")
    op.alter_column("person_educations", "person_uuid", type_=sa.String(length=64))


def downgrade() -> None:
    op.alter_column("person_educations", "person_uuid", new_column_name="person_id")
    op.alter_column("person_educations", "person_id", type_=sa.Integer())
