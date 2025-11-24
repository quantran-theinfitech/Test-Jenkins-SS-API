"""alter person position and education unique key

Revision ID: 973fc8eb77d7
Revises: 7556ebc1f312
Create Date: 2023-09-27 10:31:48.035089

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "973fc8eb77d7"
down_revision = "7556ebc1f312"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("person_career_unique_key", "person_careers", type_="unique")
    op.create_unique_constraint(
        "person_career_unique_key",
        "person_careers",
        ["media_code", "person_uuid", "career_id"],
    )
    op.drop_constraint(
        "person_education_unique_key", "person_educations", type_="unique"
    )
    op.create_unique_constraint(
        "person_education_unique_key",
        "person_educations",
        ["media_code", "person_uuid", "education_id"],
    )


def downgrade() -> None:
    op.drop_constraint("person_career_unique_key", "person_careers", type_="unique")
    op.create_unique_constraint(
        "person_career_unique_key",
        "person_careers",
        ["media_code", "person_uuid", "career_id", "start_at"],
    )
    op.drop_constraint(
        "person_education_unique_key", "person_educations", type_="unique"
    )
    op.create_unique_constraint(
        "person_education_unique_key",
        "person_educations",
        ["media_code", "person_uuid", "education_id", "start_at"],
    )
