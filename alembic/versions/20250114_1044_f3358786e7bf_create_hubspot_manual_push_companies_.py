"""create hubspot manual push companies table

Revision ID: f3358786e7bf
Revises: 78151146463f
Create Date: 2025-01-14 10:44:22.108067

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "f3358786e7bf"
down_revision = "78151146463f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hubspot_manual_push_companies",
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("log_id", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("hubspot_manual_push_companies")
