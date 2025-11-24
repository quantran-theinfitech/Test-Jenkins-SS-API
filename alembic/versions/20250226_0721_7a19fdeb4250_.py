"""empty message

Revision ID: 7a19fdeb4250
Revises: 51cae7bb87fa, e30478757879
Create Date: 2025-02-26 07:21:04.114759

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '7a19fdeb4250'
down_revision = ('51cae7bb87fa', 'e30478757879')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
