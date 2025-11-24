"""add domain to company table

Revision ID: 43fb92bbfdd5
Revises: e8a706b17f3c, aff8284f494d
Create Date: 2023-07-10 03:54:50.324655

"""
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op

# revision identifiers, used by Alembic.
revision = "43fb92bbfdd5"
down_revision = ("e8a706b17f3c", "aff8284f494d")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("domain", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("companies", "domain")
