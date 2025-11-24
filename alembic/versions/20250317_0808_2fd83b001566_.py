"""empty message

Revision ID: 2fd83b001566
Revises: 599eee8b7d2b, 12307f3e5615
Create Date: 2025-03-17 08:08:32.654179

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '2fd83b001566'
down_revision = ('599eee8b7d2b', '12307f3e5615')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
