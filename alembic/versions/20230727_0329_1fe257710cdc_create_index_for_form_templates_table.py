"""Create index for form_templates table

Revision ID: 1fe257710cdc
Revises: 6d22236e8923
Create Date: 2023-07-27 03:29:42.456635

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "1fe257710cdc"
down_revision = "6d22236e8923"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_form_templates_team_id", "form_templates", ["team_id"], unique=False
    )
    op.create_index(
        "idx_form_templates_created_at", "form_templates", ["created_at"], unique=False
    )
    op.create_index(
        "idx_form_templates_created_by", "form_templates", ["created_by"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_form_templates_created_by", table_name="form_templates")
    op.drop_index("idx_form_templates_created_at", table_name="form_templates")
    op.drop_index("idx_form_templates_team_id", table_name="form_templates")
