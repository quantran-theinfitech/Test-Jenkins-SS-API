"""Updated index education and career table

Revision ID: 04a647fbf36d
Revises: 11eb1518704a
Create Date: 2023-10-09 09:50:35.939111

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "04a647fbf36d"
down_revision = "11eb1518704a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_person_educations_person_uuid", "person_educations", ["person_uuid"]
    )
    op.create_index("idx_person_careers_person_uuid", "person_careers", ["person_uuid"])
    op.create_index("idx_persons_corporate_number", "persons", ["corporate_number"])
    op.create_index("idx_persons_uuid", "persons", ["uuid"])


def downgrade() -> None:
    op.drop_index("idx_person_educations_person_uuid")
    op.drop_index("idx_person_careers_person_uuid")
    op.drop_index("idx_persons_corporate_number")
    op.drop_index("idx_persons_uuid")
