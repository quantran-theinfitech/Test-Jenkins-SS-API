import sqlalchemy as sa

from alembic import op

revision = "d34308f3d556"
down_revision = "3940a83183d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "plans", sa.Column("mailbox_connect_quota", sa.Integer(), nullable=True)
    )
    op.execute("ALTER TYPE servicecode ADD VALUE 'MAILBOX_CONNECT'")
    op.execute(
        """
        UPDATE plans
        SET mailbox_connect_quota = CASE
            WHEN name_code = 'FRE' THEN 0
            WHEN name_code = 'SML' THEN 2
            WHEN name_code = 'STD' THEN 5
            WHEN name_code = 'PRE' THEN 15
            WHEN name_code = 'UNLIMITED' THEN 100000
            ELSE NULL
        END
        """
    )
    op.execute(
        """
        UPDATE plans
        SET send_email_quota = CASE
            WHEN name_code = 'FRE' THEN 0
            WHEN name_code = 'SML' THEN 400
            WHEN name_code = 'STD' THEN 1000
            WHEN name_code = 'PRE' THEN 3000
            WHEN name_code = 'UNLIMITED' THEN 100000
            ELSE NULL
        END
        """
    )


def downgrade() -> None:
    op.drop_column("plans", "mailbox_connect_quota")
