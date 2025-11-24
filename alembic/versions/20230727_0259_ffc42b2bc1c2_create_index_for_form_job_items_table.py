"""Create index for form_job_items table

Revision ID: ffc42b2bc1c2
Revises: c536df5df400
Create Date: 2023-07-27 02:59:10.099060

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "ffc42b2bc1c2"
down_revision = "c536df5df400"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_form_job_items_job_id", "form_job_items", ["job_id"], unique=False
    )
    op.create_index(
        "idx_form_job_items_status_code",
        "form_job_items",
        ["status_code"],
        unique=False,
    )
    op.create_index(
        "idx_form_job_items_created_at", "form_job_items", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_form_job_items_created_at", table_name="form_job_items")
    op.drop_index("idx_form_job_items_status_code", table_name="form_job_items")
    op.drop_index("idx_form_job_items_job_id", table_name="form_job_items")
