"""Added column uuid of Persons table

Revision ID: cff4c8a79f16
Revises: a56e49ad4352
Create Date: 2023-08-15 02:22:15.472667

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "cff4c8a79f16"
down_revision = "a56e49ad4352"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "persons",
        sa.Column("uuid", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("persons", "uuid")
