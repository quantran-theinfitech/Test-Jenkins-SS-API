"""empty message

Revision ID: d9feb02ebd59
Revises: fa28273388d6
Create Date: 2025-09-22 08:37:49.675915

"""
from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision = "d9feb02ebd59"
down_revision = "fa28273388d6"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index(
        "idx_recruits_corporate_start_at", table_name="recruits", if_exists=True
    )

    op.create_index(
        "idx_recruits_corporate_start_at",
        "recruits",
        [text("corporate_number"), text("start_at DESC NULLS LAST")],
    )


def downgrade():
    pass
