"""update content type

Revision ID: 102f8066f222
Revises: 3a1849fa4d63
Create Date: 2025-08-01 07:12:13.328317

"""
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "102f8066f222"
down_revision = "3a1849fa4d63"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tạm thời đổi tên cột cũ để giữ dữ liệu nếu cần
    op.alter_column(
        "sequence_step_content_items", "content", new_column_name="content_text_backup"
    )

    # Thêm cột mới kiểu LargeBinary
    op.add_column(
        "sequence_step_content_items",
        sa.Column("content", sa.LargeBinary(), nullable=True),
    )

    # Xóa cột text backup nếu không cần
    op.drop_column("sequence_step_content_items", "content_text_backup")


def downgrade() -> None:
    # Đổi tên cột binary sang tạm
    op.alter_column(
        "sequence_step_content_items",
        "content",
        new_column_name="content_binary_backup",
    )

    # Thêm lại cột text
    op.add_column(
        "sequence_step_content_items",
        sa.Column("content", sa.Text(), nullable=True),
    )

    # Xóa cột binary
    op.drop_column("sequence_step_content_items", "content_binary_backup")
