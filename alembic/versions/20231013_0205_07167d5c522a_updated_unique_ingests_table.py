"""Updated unique ingests table

Revision ID: 07167d5c522a
Revises: 2c8348503236
Create Date: 2023-10-13 02:05:51.180621

"""


from alembic import op

# revision identifiers, used by Alembic.
revision = "07167d5c522a"
down_revision = "2c8348503236"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("ingest_unique_id", "ingests", ["ingest_id"])
    op.create_index("idx_ingests_state", "ingests", ["state"])


def downgrade() -> None:
    op.drop_constraint("ingest_unique_id", "ingests", type_="unique")
    op.drop_index("idx_ingests_state")
