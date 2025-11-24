"""Update ExportStatus enum

Revision ID: abc123456789
Revises: previous_revision_id
Create Date: YYYY-MM-DD HH:MM:SS

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

# Revision identifiers, used by Alembic.
revision = '0cf5b948d4e9'
down_revision = '071a4833feac'
branch_labels = None
depends_on = None

# Define the old and new enum values
old_enum = ('IN_PROGRESS', 'AVAILABLE', 'UNAVAILABLE')
new_enum = ('IN_PROGRESS', 'AVAILABLE', 'UNAVAILABLE', 'ERROR', 'CREDIT_ERROR')

def upgrade():
    # Update the ExportStatus enum
    op.execute("ALTER TYPE exportstatus ADD VALUE 'ERROR'")
    op.execute("ALTER TYPE exportstatus ADD VALUE 'CREDIT_ERROR'")

def downgrade():
    # Downgrade logic: Remove the new value (PostgreSQL does not support removing enum values directly)
    op.execute("UPDATE export_histories SET status = 'UNAVAILABLE' WHERE status = 'ERROR' or status = 'CREDIT_ERROR'")
    op.execute("ALTER TYPE exportstatus RENAME TO exportstatus_old")
    op.execute("CREATE TYPE exportstatus AS ENUM ('IN_PROGRESS', 'AVAILABLE', 'UNAVAILABLE')")
    op.execute("ALTER TABLE export_histories ALTER COLUMN status TYPE exportstatus USING status::text::exportstatus")
    op.execute("DROP TYPE exportstatus_old")