"""add column scenarios table

Revision ID: 11b9af32663f
Revises: 92642557c8de
Create Date: 2023-10-03 03:48:52.158724

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "11b9af32663f"
down_revision = "92642557c8de"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scenarios", sa.Column("email_notification_flag", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "scenarios", sa.Column("slack_notification_flag", sa.Boolean(), nullable=True)
    )
    op.add_column("scenarios", sa.Column("type_code", sa.VARCHAR(20), nullable=True))

    op.execute("ALTER TABLE scenarios RENAME COLUMN target_emails TO target_email")
    op.execute("ALTER TABLE scenarios ALTER COLUMN target_email TYPE VARCHAR(1024)")


def downgrade() -> None:
    op.drop_column("scenarios", "email_notification_flag")
    op.drop_column("scenarios", "slack_notification_flag")
    op.drop_column("scenarios", "type_code")
    op.execute("ALTER TABLE scenarios RENAME COLUMN target_email TO target_emails")
    op.execute("ALTER TABLE scenarios ALTER COLUMN target_email TYPE VARCHAR(64)[]")
