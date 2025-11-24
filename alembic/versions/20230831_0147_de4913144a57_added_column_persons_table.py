"""Added column persons table

Revision ID: de4913144a57
Revises: d76c883961f1
Create Date: 2023-08-31 01:47:40.688407

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "de4913144a57"
down_revision = "d76c883961f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "persons",
        sa.Column("role_codes", sa.ARRAY(sa.String(length=255)), nullable=True),
    )
    op.add_column(
        "persons",
        sa.Column("role_group_codes", sa.ARRAY(sa.String(length=255)), nullable=True),
    )
    op.add_column(
        "persons",
        sa.Column("intro", sa.TEXT(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("persons", "role_codes")
    op.drop_column("persons", "role_group_codes")
