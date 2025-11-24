"""alter person_id table message_job_items

Revision ID: 5c57a5857783
Revises: 44edb1c7c388
Create Date: 2023-08-15 04:40:50.154796

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "5c57a5857783"
down_revision = "44edb1c7c388"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("message_job_items", "person_id", new_column_name="person_uuid")
    op.alter_column("message_job_items", "person_uuid", type_=sa.String(length=64))


def downgrade() -> None:
    op.alter_column("message_job_items", "person_uuid", new_column_name="person_id")
    op.alter_column("message_job_items", "person_id", type_=sa.Integer())
