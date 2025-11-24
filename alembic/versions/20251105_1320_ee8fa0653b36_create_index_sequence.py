"""create index sequence

Revision ID: ee8fa0653b36
Revises: 2c780a93a56c
Create Date: 2025-11-05 13:20:25.165115

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "ee8fa0653b36"
down_revision = "2c780a93a56c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_sequence_campaign_contacts_sequence_contact_id",
        "sequence_campaign_contacts",
        ["sequence_campaign_id", "sequence_contact_id"],
    )
    op.create_index(
        "idx_sequence_campaign_import_items_sequence_campaign_import_id",
        "sequence_campaign_import_items",
        ["sequence_campaign_import_id", "sequence_person_id"],
    )
    op.create_index(
        "idx_sequence_campaign_imports_sequence_campaign_id",
        "sequence_campaign_imports",
        ["sequence_campaign_id", "team_id"],
    )
    op.create_index(
        "idx_sequence_campaign_schedule_sending_windows_schedule_id",
        "sequence_campaign_schedule_sending_windows",
        ["schedule_id"],
    )
    op.create_index(
        "idx_sequence_campaign_schedules_team_id",
        "sequence_campaign_schedules",
        ["team_id"],
    )
    op.create_index(
        "idx_sequence_campaign_settings_sequence_campaign_id",
        "sequence_campaign_settings",
        ["sequence_campaign_id"],
    )
    op.create_index(
        "idx_sequence_campaign_steps_content_template_id_order_cp_id",
        "sequence_campaign_steps",
        ["sequence_campaign_id", "order", "content_template_id"],
    )
    op.create_index(
        "idx_sequence_contacts_sequence_campaign_id",
        "sequence_contacts",
        ["sequence_campaign_id"],
    )
    op.create_index(
        "idx_sequence_email_schedules_mail_history_id",
        "sequence_email_schedules",
        ["mail_history_id"],
    )
    op.create_index(
        "idx_sequence_mail_alias_settings_campaign_id_person_id_step_id",
        "sequence_mail_alias_settings",
        ["sequence_campaign_id", "sequence_person_id", "sequence_step_id"],
    )
    op.create_index(
        "idx_sequence_mail_aliases_sequence_mailbox_id",
        "sequence_mail_aliases",
        ["sequence_mailbox_id"],
    )
    op.create_index(
        "idx_sequence_mail_histories_contact_id_campaign_id_step_id",
        "sequence_mail_histories",
        ["sequence_contact_id", "sequence_campaign_id", "sequence_step_id"],
    )
    op.create_index("idx_sequence_mailboxes_team_id", "sequence_mailboxes", ["team_id"])
    op.create_index(
        "idx_sequence_person_statistics_sequence_person_id",
        "sequence_person_statistics",
        ["sequence_person_id"],
    )
    op.create_index(
        "idx_sequence_tasks_sequence_campaign_id_step_id_person_id",
        "sequence_tasks",
        ["sequence_campaign_id", "sequence_step_id", "sequence_person_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_sequence_campaign_contacts_sequence_contact_id",
        table_name="sequence_campaign_contacts",
    )
    op.drop_index(
        "idx_sequence_campaign_import_items_sequence_campaign_import_id",
        table_name="sequence_campaign_import_items",
    )
    op.drop_index(
        "idx_sequence_campaign_imports_sequence_campaign_id",
        table_name="sequence_campaign_imports",
    )
    op.drop_index(
        "idx_sequence_campaign_schedule_sending_windows_schedule_id",
        table_name="sequence_campaign_schedule_sending_windows",
    )
    op.drop_index(
        "idx_sequence_campaign_schedules_team_id",
        table_name="sequence_campaign_schedules",
    )
    op.drop_index(
        "idx_sequence_campaign_settings_sequence_campaign_id",
        table_name="sequence_campaign_settings",
    )
    op.drop_index(
        "idx_sequence_campaign_steps_content_template_id_order_cp_id",
        table_name="sequence_campaign_steps",
    )
    op.drop_index(
        "idx_sequence_contacts_sequence_campaign_id", table_name="sequence_contacts"
    )
    op.drop_index(
        "idx_sequence_email_schedules_mail_history_id",
        table_name="sequence_email_schedules",
    )
    op.drop_index(
        "idx_sequence_mail_alias_settings_campaign_id_person_id_step_id",
        table_name="sequence_mail_alias_settings",
    )
    op.drop_index(
        "idx_sequence_mail_aliases_sequence_mailbox_id",
        table_name="sequence_mail_aliases",
    )
    op.drop_index(
        "idx_sequence_mail_histories_contact_id_campaign_id_step_id",
        table_name="sequence_mail_histories",
    )
    op.drop_index("idx_sequence_mailboxes_team_id", table_name="sequence_mailboxes")
    op.drop_index(
        "idx_sequence_person_statistics_sequence_person_id",
        table_name="sequence_person_statistics",
    )
    op.drop_index(
        "idx_sequence_tasks_sequence_campaign_id_step_id_person_id",
        table_name="sequence_tasks",
    )
