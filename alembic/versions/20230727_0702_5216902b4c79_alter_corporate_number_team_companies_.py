"""alter_corporate_number_team_companies_table

Revision ID: 5216902b4c79
Revises: a32eef60c122
Create Date: 2023-07-27 07:02:30.642808

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "5216902b4c79"
down_revision = "a32eef60c122"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("team_companies", "corporate_number", type_=sa.String(length=64))


def downgrade() -> None:
    op.alter_column("team_companies", "corporate_number", type_=sa.TEXT())
