"""empty message

Revision ID: de9cfc6c7ae9
Revises: 25cb0c324ee1
Create Date: 2025-05-13 07:51:57.947927

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "de9cfc6c7ae9"
down_revision = "25cb0c324ee1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sequence_campaign_schedule_sending_windows",
        sa.Column(
            "created_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "updated_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("schedule_id", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.Integer(), nullable=True),
        sa.Column("end_time", sa.Integer(), nullable=True),
        sa.Column("week_day", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column(
        "sequence_campaign_schedules",
        sa.Column("name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "sequence_campaign_schedules",
        sa.Column("time_zone", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "sequence_campaign_schedules",
        sa.Column("use_local_time_zone", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "sequence_campaign_schedules",
        sa.Column("is_skip_holiday", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "sequence_campaign_schedules",
        sa.Column("days_per_week", postgresql.ARRAY(sa.Integer()), nullable=True),
    )
    op.add_column(
        "sequence_campaign_schedules",
        sa.Column("is_default", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sequence_campaign_schedules", "is_skip_holiday")
    op.drop_column("sequence_campaign_schedules", "use_local_time_zone")
    op.drop_column("sequence_campaign_schedules", "time_zone")
    op.drop_column("sequence_campaign_schedules", "name")
    op.drop_column("sequence_campaign_schedules", "days_per_week")
    op.drop_column("sequence_campaign_schedules", "is_default")
    op.drop_table("sequence_campaign_schedule_sending_windows")
