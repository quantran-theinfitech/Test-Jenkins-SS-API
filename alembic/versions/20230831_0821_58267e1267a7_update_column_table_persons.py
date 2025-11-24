"""update column table persons

Revision ID: 58267e1267a7
Revises: de4913144a57
Create Date: 2023-08-31 08:21:30.749559

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "58267e1267a7"
down_revision = "de4913144a57"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("persons", "role_code")
    op.alter_column("persons", "role_codes", new_column_name="role_code")
    op.alter_column("persons", "role_code", type_=sa.String(length=255))


def downgrade() -> None:
    op.alter_column("persons", "role_code", new_column_name="role_codes")
    op.execute(
        "ALTER TABLE persons "
        "ALTER COLUMN role_codes TYPE character varying(255)[] "
        "USING role_codes::character varying(255)[];"
    )
    op.add_column(
        "persons",
        sa.Column("role_code", sa.String(length=20), nullable=True),
    )
