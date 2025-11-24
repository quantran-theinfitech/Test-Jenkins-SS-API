"""drop cols sequence_person_statistics

Revision ID: 654400f43989
Revises: 02e0b2bd2d8c
Create Date: 2025-05-20 14:34:05.402491

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "654400f43989"
down_revision = "02e0b2bd2d8c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("sequence_person_statistics", "uuid")
    op.drop_column("sequence_person_statistics", "sequence_campaign_id")
    op.drop_column("sequence_person_statistics", "name")
    op.drop_column("sequence_person_statistics", "role_name")
    op.drop_column("sequence_person_statistics", "email")
    op.drop_column("sequence_person_statistics", "linkedin_url")
    op.drop_column("sequence_person_statistics", "twitter_url")
    op.drop_column("sequence_person_statistics", "github_url")
    op.drop_column("sequence_person_statistics", "note_url")
    op.drop_column("sequence_person_statistics", "fb_url")
    op.drop_column("sequence_person_statistics", "wantedly_url")
    op.drop_column("sequence_person_statistics", "skills")
    op.drop_column("sequence_person_statistics", "corporate_number")
    op.drop_column("sequence_person_statistics", "status")
    op.drop_column("sequence_person_statistics", "current_step")
    op.drop_column("sequence_person_statistics", "stage")
    op.drop_column("sequence_person_statistics", "company_name")
    op.drop_column("sequence_person_statistics", "wantedly_id")
    op.drop_column("sequence_person_statistics", "address")
    op.drop_column("sequence_person_statistics", "linkedin_internal_id")
    op.drop_column("sequence_person_statistics", "intro")
    op.drop_column("sequence_person_statistics", "bio")
    op.drop_column("sequence_person_statistics", "role_code")
    op.drop_column("sequence_person_statistics", "role_group_codes")
    op.add_column(
        "sequence_person_statistics",
        sa.Column("sequence_person_id", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sequence_person_statistics", "sequence_person_id")
    op.add_column(
        "sequence_person_statistics",
        sa.Column("uuid", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("sequence_campaign_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("role_name", sa.ARRAY(sa.Text()), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("email", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("linkedin_url", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("twitter_url", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("github_url", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("note_url", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("fb_url", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("wantedly_url", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("skills", sa.Text(), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("corporate_number", sa.ARRAY(sa.String(length=64)), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("status", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("current_step", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("stage", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("company_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("wantedly_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("address", sa.Text(), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("linkedin_internal_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("intro", sa.Text(), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("bio", sa.Text(), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("role_code", sa.Text(), nullable=True),
    )
    op.add_column(
        "sequence_person_statistics",
        sa.Column("role_group_codes", sa.ARRAY(sa.String(length=255)), nullable=True),
    )
