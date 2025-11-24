"""add job_columns table recruits

Revision ID: a0b67681316d
Revises: d5dfedd98791
Create Date: 2025-06-12 08:37:50.823624

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a0b67681316d"
down_revision = "d5dfedd98791"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "recruits",
        sa.Column("job_positions", sa.ARRAY(sa.String(length=255)), nullable=True),
    )
    op.add_column(
        "recruits", sa.Column("scores", sa.ARRAY(sa.String(length=255)), nullable=True)
    )
    op.add_column(
        "recruits",
        sa.Column("job_categories", sa.ARRAY(sa.String(length=255)), nullable=True),
    )
    op.add_column(
        "recruits",
        sa.Column("job_sub_categories", sa.ARRAY(sa.String(length=255)), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("recruits", "job_sub_categories")
    op.drop_column("recruits", "job_categories")
    op.drop_column("recruits", "scores")
    op.drop_column("recruits", "job_positions")
