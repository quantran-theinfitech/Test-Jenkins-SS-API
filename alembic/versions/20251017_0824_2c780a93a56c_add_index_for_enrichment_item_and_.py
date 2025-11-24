"""add_index_for_enrichment_item_and_enrichment_item_data_table

Revision ID: 2c780a93a56c
Revises: fee9d32b852c
Create Date: 2025-10-17 08:24:44.044522

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2c780a93a56c"
down_revision = "fee9d32b852c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Indexes for enrichment_items table
    op.create_index(
        "idx_enrichment_items_enrichment_id_deleted_at",
        "enrichment_items",
        ["enrichment_id", "deleted_at"],
    )

    op.create_index(
        "idx_enrichment_items_enrichment_file_id_deleted_at",
        "enrichment_items",
        ["enrichment_file_id", "deleted_at"],
    )

    op.create_index("idx_enrichment_items_status", "enrichment_items", ["status"])

    # Indexes for enrichment_item_data table
    op.create_index(
        "idx_enrichment_item_data_item_id_mapping_id_deleted_at",
        "enrichment_item_data",
        ["enrichment_item_id", "column_json_mapping_id", "deleted_at"],
    )

    op.create_index(
        "idx_enrichment_item_data_mapping_id_deleted_at",
        "enrichment_item_data",
        ["column_json_mapping_id", "deleted_at"],
    )

    op.create_index(
        "idx_enrichment_item_data_item_id_deleted_at",
        "enrichment_item_data",
        ["enrichment_item_id", "deleted_at"],
    )


def downgrade() -> None:
    # Drop indexes for enrichment_item_data table
    op.drop_index("idx_enrichment_item_data_item_id_deleted_at", "enrichment_item_data")
    op.drop_index(
        "idx_enrichment_item_data_mapping_id_deleted_at", "enrichment_item_data"
    )
    op.drop_index(
        "idx_enrichment_item_data_item_id_mapping_id_deleted_at", "enrichment_item_data"
    )

    # Drop indexes for enrichment_items table
    op.drop_index("idx_enrichment_items_status", "enrichment_items")
    op.drop_index(
        "idx_enrichment_items_enrichment_file_id_deleted_at", "enrichment_items"
    )
    op.drop_index("idx_enrichment_items_enrichment_id_deleted_at", "enrichment_items")
