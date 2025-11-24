"""Create index for form_jobs table

Revision ID: abdcc7ea3bcf
Revises: ffc42b2bc1c2
Create Date: 2023-07-27 03:04:00.645514

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "abdcc7ea3bcf"
down_revision = "ffc42b2bc1c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("idx_form_jobs_team_id", "form_jobs", ["team_id"], unique=False)
    op.create_index(
        "idx_form_jobs_target_collection_id",
        "form_jobs",
        ["target_collection_id"],
        unique=False,
    )
    op.create_index(
        "idx_form_jobs_exclude_collection_id",
        "form_jobs",
        ["exclude_collection_id"],
        unique=False,
    )
    op.create_index(
        "idx_form_jobs_template_id", "form_jobs", ["template_id"], unique=False
    )
    op.create_index(
        "idx_form_jobs_placeholder_id", "form_jobs", ["placeholder_id"], unique=False
    )
    op.create_index(
        "idx_form_jobs_created_at", "form_jobs", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_form_jobs_created_at", table_name="form_jobs")
    op.drop_index("idx_form_jobs_placeholder_id", table_name="form_jobs")
    op.drop_index("idx_form_jobs_template_id", table_name="form_jobs")
    op.drop_index("idx_form_jobs_exclude_collection_id", table_name="form_jobs")
    op.drop_index("idx_form_jobs_target_collection_id", table_name="form_jobs")
    op.drop_index("idx_form_jobs_team_id", table_name="form_jobs")
