"""add-col-type-code-and-company-custom-id

Revision ID: 786b05eb1289
Revises: 60ccbdb06c36
Create Date: 2025-02-20 10:16:05.240612

"""

import sqlalchemy as sa

from alembic import op

formjob_type_enum = sa.Enum("SYS", "CSV", name="formjobtypecode")

# revision identifiers, used by Alembic.
revision = "786b05eb1289"
down_revision = "ac0a828ad0f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    formjob_type_enum.create(op.get_bind())
    op.add_column(
        "form_job_items",
        sa.Column("company_custom_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "form_jobs",
        sa.Column("type_code", formjob_type_enum, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("form_jobs", "type_code")
    op.drop_column("form_job_items", "company_custom_id")
    formjob_type_enum.drop(op.get_bind())
