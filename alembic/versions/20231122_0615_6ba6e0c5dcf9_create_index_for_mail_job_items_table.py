"""create index for mail job items table

Revision ID: 6ba6e0c5dcf9
Revises: c9cb9c7f141f
Create Date: 2023-11-22 06:15:44.425954

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "6ba6e0c5dcf9"
down_revision = "c9cb9c7f141f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_mail_job_items_job_id", "mail_job_items", ["job_id"], unique=False
    )
    op.create_index(
        "idx_mail_job_items_status_code",
        "mail_job_items",
        ["status_code"],
        unique=False,
    )
    op.create_index(
        "idx_mail_job_items_created_at", "mail_job_items", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_mail_job_items_created_at", table_name="mail_job_items")
    op.drop_index("idx_mail_job_items_status_code", table_name="mail_job_items")
    op.drop_index("idx_mail_job_items_job_id", table_name="mail_job_items")
