"""create table search histories

Revision ID: b9cf7c9389f7
Revises: ee8fa0653b36
Create Date: 2025-10-30 10:10:03.978440

"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "b9cf7c9389f7"
down_revision = "ee8fa0653b36"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "search_histories",
        sa.Column(
            "type",
            sa.Enum("PERSON", "COMPANY", name="search_history_enum"),
            nullable=True,
        ),
        sa.Column("prompt_message", sa.Text(), nullable=True),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("search_histories")
