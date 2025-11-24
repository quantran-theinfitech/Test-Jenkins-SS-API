"""create index for mail jobs table

Revision ID: c9cb9c7f141f
Revises: 678f8a933b89
Create Date: 2023-11-22 04:10:56.776738

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "c9cb9c7f141f"
down_revision = "678f8a933b89"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("idx_mail_jobs_team_id", "mail_jobs", ["team_id"], unique=False)
    op.create_index(
        "idx_mail_jobs_target_collection_id",
        "mail_jobs",
        ["target_collection_id"],
        unique=False,
    )
    op.create_index(
        "idx_mail_jobs_exclude_collection_id",
        "mail_jobs",
        ["exclude_collection_id"],
        unique=False,
    )
    op.create_index(
        "idx_mail_jobs_template_id", "mail_jobs", ["template_id"], unique=False
    )
    op.create_index(
        "idx_mail_jobs_placeholder_id", "mail_jobs", ["placeholder_id"], unique=False
    )
    op.create_index(
        "idx_mail_jobs_created_at", "mail_jobs", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_mail_jobs_created_at", table_name="mail_jobs")
    op.drop_index("idx_mail_jobs_placeholder_id", table_name="mail_jobs")
    op.drop_index("idx_mail_jobs_template_id", table_name="mail_jobs")
    op.drop_index("idx_mail_jobs_exclude_collection_id", table_name="mail_jobs")
    op.drop_index("idx_mail_jobs_target_collection_id", table_name="mail_jobs")
    op.drop_index("idx_mail_jobs_team_id", table_name="mail_jobs")
