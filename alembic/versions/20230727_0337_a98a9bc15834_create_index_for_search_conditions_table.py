"""Create index for search_conditions table

Revision ID: a98a9bc15834
Revises: 49f126945e83
Create Date: 2023-07-27 03:37:55.114130

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a98a9bc15834"
down_revision = "49f126945e83"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_search_conditions_user_id", "search_conditions", ["user_id"], unique=False
    )
    op.create_index(
        "idx_search_conditions_model_code",
        "search_conditions",
        ["model_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_search_conditions_model_code", table_name="search_conditions")
    op.drop_index("idx_search_conditions_user_id", table_name="search_conditions")
