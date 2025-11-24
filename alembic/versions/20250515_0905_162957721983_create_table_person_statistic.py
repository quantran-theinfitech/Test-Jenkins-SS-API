"""create table person statistic

Revision ID: 162957721983
Revises: abeccc619b4c
Create Date: 2025-05-15 09:05:43.778592

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "162957721983"
down_revision = "abeccc619b4c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sequence_person_statistics",
        sa.Column("uuid", sa.String(length=64), nullable=True),
        sa.Column("sequence_campaign_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("role_name", sa.ARRAY(sa.Text()), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("linkedin_url", sa.String(length=1024), nullable=True),
        sa.Column("twitter_url", sa.String(length=1024), nullable=True),
        sa.Column("github_url", sa.String(length=1024), nullable=True),
        sa.Column("note_url", sa.String(length=1024), nullable=True),
        sa.Column("fb_url", sa.String(length=1024), nullable=True),
        sa.Column("wantedly_url", sa.String(length=1024), nullable=True),
        sa.Column("skills", sa.Text(), nullable=True),
        sa.Column("corporate_number", sa.ARRAY(sa.String(length=64)), nullable=True),
        sa.Column("company_name", sa.ARRAY(sa.String(length=255)), nullable=True),
        sa.Column("wantedly_id", sa.String(length=255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("linkedin_internal_id", sa.String(length=255), nullable=True),
        sa.Column("intro", sa.Text(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("role_code", sa.Text(), nullable=True),
        sa.Column("role_group_codes", sa.ARRAY(sa.String(length=255)), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "updated_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.Column("status", sa.String(length=64), nullable=True),
        sa.Column("current_step", sa.Integer(), nullable=True),
        sa.Column("stage", sa.String(length=64), nullable=True),
        sa.Column("last_activity", sa.TIMESTAMP(), nullable=True),
        sa.Column("email_last_opened_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("email_last_clicked_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("times_opened", sa.Integer(), nullable=True),
        sa.Column("times_clicked", sa.Integer(), nullable=True),
    )
    op.execute(
        """
        ALTER TABLE sequence_person_statistics
        ALTER COLUMN stage TYPE sequencepersonstage
        USING stage::sequencepersonstage;
    """
    )


def downgrade() -> None:
    op.drop_table("sequence_person_statistics")
