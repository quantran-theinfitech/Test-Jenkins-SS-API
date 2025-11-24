"""add_email_signature_and_opt_out_message

Revision ID: da39e22e609b
Revises: f5ac93e3bd40
Create Date: 2025-07-17 07:05:34.371452

"""
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "da39e22e609b"
down_revision = "f5ac93e3bd40"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "sequence_mail_histories",
        sa.Column("email_signature", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "sequence_mail_histories",
        sa.Column("opt_out_message", sa.String(length=255), nullable=True),
    )


def downgrade():
    op.drop_column("sequence_mail_histories", "opt_out_message")
    op.drop_column("sequence_mail_histories", "email_signature")
