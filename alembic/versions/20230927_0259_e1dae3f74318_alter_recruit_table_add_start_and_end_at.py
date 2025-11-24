"""alter recruit table add start and end at

Revision ID: e1dae3f74318
Revises: 7556ebc1f312
Create Date: 2023-09-27 02:59:56.852965

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e1dae3f74318"
down_revision = "7556ebc1f312"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "recruits",
        sa.Column("start_at", sa.TIMESTAMP(), nullable=True),
    )
    op.add_column(
        "recruits",
        sa.Column("end_at", sa.TIMESTAMP(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("recruits", "start_at")
    op.drop_column("recruits", "end_at")
