"""add unique key person uuid

Revision ID: 928421509477
Revises: 8a3af854f452
Create Date: 2023-09-07 09:31:31.798165

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "928421509477"
down_revision = "8a3af854f452"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "persons", sa.Column("company_name", sa.String(length=255), nullable=True)
    )
    op.alter_column("persons", "role_name", type_=sa.Text(), nullable=True)
    op.alter_column("persons", "role_code", type_=sa.Text(), nullable=True)
    op.alter_column(
        "persons", "linkedin_internal_id", type_=sa.VARCHAR(length=1024), nullable=True
    )
    op.create_unique_constraint("person_unique_uuid", "persons", ["uuid"])


def downgrade() -> None:
    op.drop_constraint("person_unique_uuid", "persons", type_="unique")
    op.alter_column("persons", "role_code", type_=sa.VARCHAR(length=255), nullable=True)
    op.alter_column("persons", "role_name", type_=sa.VARCHAR(length=255), nullable=True)
    op.alter_column(
        "persons", "linkedin_internal_id", type_=sa.VARCHAR(length=255), nullable=True
    )
    op.drop_column("persons", "company_name")
