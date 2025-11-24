"""update_hubspot_integrations_table

Revision ID: 78151146463f
Revises: a8e096dcfed5
Create Date: 2025-01-14 06:35:18.923730

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "78151146463f"
down_revision = "a8e096dcfed5"
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.add_column(
        "hubspot_company_multiple_pull_histories",
        sa.Column("hubspot_pull_log_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "hubspot_company_multiple_push_histories",
        sa.Column("hubspot_push_log_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "hubspot_company_not_found_pull_histories",
        sa.Column("hubspot_push_log_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "hubspot_company_not_found_push_histories",
        sa.Column("hubspot_push_log_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "hubspot_company_pull_histories",
        sa.Column("log_id", sa.String(length=50), nullable=True),
    )
    op.drop_column("hubspot_company_pull_histories", "error_detail_id")

    op.add_column(
        "hubspot_company_push_histories",
        sa.Column("log_id", sa.String(length=50), nullable=True),
    )
    op.drop_column("hubspot_company_push_histories", "error_detail_id")

    op.drop_column("hubspot_synced_companies", "overwrite_flag")
    op.drop_column("hubspot_synced_companies", "autofill_flag")

    op.add_column(
        "hubspot_synced_companies",
        sa.Column("hubspot_company_id", sa.Integer(), nullable=True),
    )
    op.drop_column("hubspot_company_sync_histories", "sync_id")

    op.add_column(
        "hubspot_company_sync_histories",
        sa.Column("log_id", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "hubspot_company_sync_histories",
        sa.Column("status", sa.Integer(), nullable=True),
    )
    op.create_index(
        "idx_hubspot_company_sync_histories_log_id",
        "hubspot_company_sync_histories",
        ["log_id"],
    )


def downgrade() -> None:
    # Re-add "error_detail_id" column to "hubspot_company_pull_histories"
    op.add_column(
        "hubspot_company_pull_histories",
        sa.Column("error_detail_id", sa.Integer(), nullable=True),
    )
    op.drop_column("hubspot_company_pull_histories", "log_id")

    # Re-add "error_detail_id" column to "hubspot_company_push_histories"
    op.add_column(
        "hubspot_company_push_histories",
        sa.Column("error_detail_id", sa.Integer(), nullable=True),
    )
    op.drop_column("hubspot_company_push_histories", "log_id")

    # Re-add "overwrite_flag" and "autofill_flag" columns to "hubspot_synced_companies"
    op.add_column(
        "hubspot_synced_companies",
        sa.Column("overwrite_flag", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "hubspot_synced_companies",
        sa.Column("autofill_flag", sa.Boolean(), nullable=True),
    )
    op.drop_column("hubspot_synced_companies", "hubspot_company_id")

    # Re-add "sync_id" column to "hubspot_company_sync_histories"
    op.add_column(
        "hubspot_company_sync_histories",
        sa.Column("sync_id", sa.Integer(), nullable=True),
    )
    # Drop index on "log_id" in "hubspot_company_sync_histories"
    op.drop_index("idx_hubspot_company_sync_histories_log_id")

    op.drop_column("hubspot_company_sync_histories", "log_id")
    op.drop_column("hubspot_company_sync_histories", "status")

    # Remove added columns from "hubspot_company_multiple_pull_histories"
    op.drop_column("hubspot_company_multiple_pull_histories", "hubspot_pull_log_id")

    # Remove added columns from "hubspot_company_multiple_push_histories"
    op.drop_column("hubspot_company_multiple_push_histories", "hubspot_push_log_id")

    # Remove added columns from "hubspot_company_not_found_pull_histories"
    op.drop_column("hubspot_company_not_found_pull_histories", "hubspot_push_log_id")

    # Remove added columns from "hubspot_company_not_found_push_histories"
    op.drop_column("hubspot_company_not_found_push_histories", "hubspot_push_log_id")
