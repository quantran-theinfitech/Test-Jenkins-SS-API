"""Update team_credits table

Revision ID: cc416d1720c3
Revises: 0c7189ebde6b
Create Date: 2023-10-17 04:20:55.949310

"""
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "cc416d1720c3"
down_revision = "0c7189ebde6b"
branch_labels = None
depends_on = None


old_service_code = postgresql.ENUM("CPN", "PERSON", "MSG", "CTF", name="servicecode")

new_service_code = postgresql.ENUM(
    "CPN", "PERSON", "MSG", "CTF", "SCENARIO", name="servicecode"
)

old_reason_code = postgresql.ENUM(
    "MONTHLY", "COMPENSATE", "EXCHANGED", name="reasoncode"
)

new_reason_code = postgresql.ENUM(
    "MONTHLY", "COMPENSATE", "EXCHANGED", "INIT", name="reasoncode"
)


def upgrade() -> None:
    op.execute("ALTER TYPE servicecode ADD VALUE 'SCENARIO'")
    op.execute("ALTER TYPE reasoncode ADD VALUE 'INIT'")


def downgrade() -> None:
    # Postgresql not support drop a value of enum type

    # Change column type to varchar
    op.execute(
        'ALTER TABLE team_credits ALTER COLUMN "service_code" '
        'TYPE varchar USING "service_code"::varchar'
    )
    op.execute(
        'ALTER TABLE downloaded_histories ALTER COLUMN "service_code" '
        'TYPE varchar USING "service_code"::varchar'
    )

    op.execute(
        'ALTER TABLE team_credits ALTER COLUMN "reason_code" '
        'TYPE varchar USING "reason_code"::varchar'
    )

    # Update new value of enum type to NULL
    op.execute(
        "UPDATE team_credits set service_code=NULL WHERE service_code = 'SCENARIO'"
    )
    op.execute(
        """UPDATE downloaded_histories set service_code=NULL
        WHERE service_code = 'SCENARIO'"""
    )

    op.execute("UPDATE team_credits set reason_code=NULL WHERE reason_code = 'INIT'")

    # Drop new type
    new_service_code.drop(op.get_bind())
    new_reason_code.drop(op.get_bind())

    # Re create old type
    old_service_code.create(op.get_bind())
    old_reason_code.create(op.get_bind())

    # Change column type to old type
    op.execute(
        "ALTER TABLE team_credits ALTER COLUMN "
        "service_code TYPE servicecode"
        " USING service_code::text::servicecode"
    )
    op.execute(
        "ALTER TABLE downloaded_histories ALTER COLUMN "
        "service_code TYPE servicecode"
        " USING service_code::text::servicecode"
    )

    op.execute(
        "ALTER TABLE team_credits ALTER COLUMN "
        "reason_code TYPE reasoncode"
        " USING reason_code::text::reasoncode"
    )
