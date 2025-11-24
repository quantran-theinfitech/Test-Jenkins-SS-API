"""alter table person careers and educations add corporate number,...

Revision ID: 95a4b031a907
Revises: e56d8dbd1fb9
Create Date: 2023-09-15 07:53:42.119342

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "95a4b031a907"
down_revision = "e56d8dbd1fb9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "person_careers",
        sa.Column("corporate_number", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "person_careers",
        sa.Column("media_code", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "person_educations",
        sa.Column("media_code", sa.String(length=20), nullable=True),
    )
    op.create_unique_constraint(
        "person_career_unique_key",
        "person_careers",
        [
            "person_uuid",
            "company_id",
            "company_name",
            "start_at",
            "role_name",
            "description",
            "media_code",
        ],
    )
    op.create_unique_constraint(
        "person_education_unique_key",
        "person_educations",
        [
            "person_uuid",
            "school_name",
            "start_at",
            "major",
            "description",
            "media_code",
        ],
    )


def downgrade() -> None:
    op.drop_column("person_careers", "corporate_number")
    op.drop_column("person_careers", "media_code")
    op.drop_column("person_educations", "media_code")
    op.drop_constraint("person_career_unique_key", "person_careers", type_="unique")
    op.drop_constraint(
        "person_education_unique_key", "person_educations", type_="unique"
    )
