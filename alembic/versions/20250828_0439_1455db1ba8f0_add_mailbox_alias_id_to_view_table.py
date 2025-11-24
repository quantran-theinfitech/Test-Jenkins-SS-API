"""add mailbox_alias_id to view table

Revision ID: 1455db1ba8f0
Revises: 7a4cfe2632a9
Create Date: 2025-08-28 04:39:34.493293

"""
from alembic import op
from app.models.sequence.mail_history import MAIL_HISTORY_VIEW_NAME

# revision identifiers, used by Alembic.
revision = "1455db1ba8f0"
down_revision = "c627106f135b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(f"DROP VIEW IF EXISTS {MAIL_HISTORY_VIEW_NAME};")
    op.execute(
        f"""
    CREATE OR REPLACE VIEW {MAIL_HISTORY_VIEW_NAME} AS (
        SELECT smh.id AS mail_history_id,
            smh.sequence_person_id,
            sp."name" AS sequence_person_name,
            smh.sequence_campaign_id,
            sc."name" AS sequence_campaign_name,
            smh.sequence_step_id,
            scs."order" AS sequence_step_order,
            smh.sequence_mailbox_id,
            smas.mailbox_alias_id,
            sm.email AS email_from,
            smh.title,
            smh."content",
            smh.email_to,
            smh.status,
            smh.sent_at,
            smh.sent_by,
            u."name" AS sender_name,
            'HISTORY' AS mail_history_type,
            smh.process_status AS process_status,
            smh.thread_id AS thread_id,
            smt.is_reply_to_previous_thread AS is_reply_to_previous_thread,
            smh.is_include_opt_out_and_signature,
            smh.email_signature,
            smh.opt_out_message
        FROM sequence_mail_histories smh
        JOIN sequence_campaign_steps scs ON smh.sequence_step_id = scs.id
        JOIN sequence_step_content_templates smt ON scs.content_template_id = smt.id
        JOIN sequence_campaigns sc ON smh.sequence_campaign_id = sc.id
        JOIN sequence_contacts sp ON smh.sequence_person_id = sp.id
        LEFT JOIN sequence_mailboxes sm ON smh.sequence_mailbox_id = sm.id
        LEFT JOIN sequence_mail_alias_settings smas ON smas.mailbox_id = smh.sequence_mailbox_id AND smas.sequence_campaign_id = smh.sequence_campaign_id AND smas.sequence_person_id = smh.sequence_person_id
        LEFT JOIN users u ON smh.sent_by = u.id
        WHERE smh.deleted_at IS NULL
        UNION
            SELECT NULL as mail_history_id,
                tmp.sequence_person_id,
                tmp.sequence_person_name,
                tmp.sequence_campaign_id,
                tmp.sequence_campaign_name,
                tmp.next_sequence_step_id AS sequence_step_id,
                tmp.sequence_step_order,
                tmp.sequence_mailbox_id,
                tmp.mailbox_alias_id,
                tmp.email_from,
                tmp.mail_template_title AS title,
                tmp.mail_template_content AS content,
                tmp.email_to,
                'SCHEDULED' AS status,
                CASE
                    WHEN tmp.timing_type = 'IMMEDIATE'::timingtype
                            AND tmp.step_type = 'MAIL_AUTO'::steptype
                            AND (tmp.sequence_step_activated_at IS NOT NULL AND tmp.sequence_step_activated_at >= tmp.sent_at AND tmp.sequence_step_activated_at >= tmp.sequence_person_time_resumed)
                        THEN tmp.sequence_step_activated_at
                    WHEN tmp.timing_type = 'SCHEDULED'
                            AND tmp.step_type = 'MAIL_AUTO'
                            AND (tmp.sequence_step_activated_at IS NOT NULL AND tmp.sequence_step_activated_at >= tmp.sent_at AND tmp.sequence_step_activated_at >= tmp.sequence_person_time_resumed)
                        THEN tmp.sequence_step_activated_at + (tmp.schedule_value || ' ' || tmp.schedule_unit)::interval
                    WHEN tmp.timing_type = 'SCHEDULED'
                            AND tmp.step_type = 'MAIL_AUTO'
                            AND ((tmp.sequence_step_activated_at IS NULL OR tmp.sent_at >= tmp.sequence_step_activated_at) AND tmp.sent_at >= tmp.sequence_person_time_resumed)
                        THEN tmp.sent_at + (tmp.schedule_value || ' ' || tmp.schedule_unit)::interval
                    WHEN tmp.timing_type = 'IMMEDIATE'::timingtype
                            AND tmp.step_type = 'MAIL_AUTO'::steptype
                            AND ((tmp.sequence_step_activated_at IS NULL OR tmp.sent_at >= tmp.sequence_step_activated_at) AND tmp.sent_at >= tmp.sequence_person_time_resumed)
                        THEN tmp.sent_at
                    WHEN tmp.timing_type = 'SCHEDULED'
                            AND tmp.step_type = 'MAIL_AUTO'
                            AND (tmp.sequence_person_time_resumed >= tmp.sent_at AND (tmp.sequence_step_activated_at IS NULL OR tmp.sequence_person_time_resumed >= tmp.sequence_step_activated_at))
                        THEN tmp.sequence_person_time_resumed + (tmp.schedule_value || ' ' || tmp.schedule_unit)::interval
                    WHEN tmp.timing_type = 'IMMEDIATE'::timingtype
                            AND tmp.step_type = 'MAIL_AUTO'::steptype
                            AND (tmp.sequence_person_time_resumed >= tmp.sent_at AND (tmp.sequence_step_activated_at IS NULL OR tmp.sequence_person_time_resumed >= tmp.sequence_step_activated_at))
                        THEN tmp.sequence_person_time_resumed
                    ELSE NULL::timestamp without time zone
                END AS sent_at,
                tmp.sent_by,
                tmp.sender_name,
                'FUTURE' AS mail_history_type,
                NULL AS process_status,
                CASE WHEN tmp.is_reply_to_previous_thread THEN tmp.thread_id ELSE NULL END AS thread_id,
                tmp.is_reply_to_previous_thread AS is_reply_to_previous_thread,
                tmp.is_opt_out_message_after_signature as is_include_opt_out_and_signature,
                -- SỬA
                tmp.mailbox_email_signature as email_signature,
                tmp.mailbox_opt_out_message_after_signature as opt_out_message
            FROM
            (SELECT smh.*,
                    scs.timing_type,
                    scs.schedule_unit,
                    scs.schedule_value,
                    scs.step_type,
                    scs.activated_at AS sequence_step_activated_at,
                    scs."is_active" AS is_sequence_step_active,
                    sp.name AS sequence_person_name,
                    sc.name AS sequence_campaign_name,
                    scp.status AS sequence_person_status,
                    scs."order" AS sequence_step_order,
                    sm.email AS email_from,
                    smt.title AS mail_template_title,
                    u."name" AS sender_name,
                    smt."content" AS mail_template_content,
                    smt.is_reply_to_previous_thread AS is_reply_to_previous_thread,
                    scp.time_resumed AS sequence_person_time_resumed,
                    sm.is_opt_out_message_after_signature AS is_opt_out_message_after_signature,
                    -- Sửa
                    sm.email_signature AS mailbox_email_signature,
                    sm.opt_out_message_after_signature AS mailbox_opt_out_message_after_signature,
                    ROW_NUMBER() OVER (PARTITION BY smh.sequence_campaign_id, smh.sequence_person_id
                                        ORDER BY scs.order DESC) AS row_num
            FROM sequence_mail_histories smh
                LEFT JOIN sequence_campaign_steps scs ON smh.next_sequence_step_id = scs.id
                LEFT JOIN sequence_step_content_templates smt ON scs.content_template_id = smt.id
                JOIN sequence_campaigns sc ON smh.sequence_campaign_id = sc.id AND sc.deleted_at IS NULL AND sc.is_active = TRUE
                JOIN sequence_contacts sp ON smh.sequence_person_id = sp.id AND sp.deleted_at IS NULL
                JOIN sequence_campaign_contacts scp ON scp.sequence_contact_id = sp.id AND scp.sequence_campaign_id = sc.id AND scp.deleted_at IS NULL
                LEFT JOIN sequence_mailboxes sm ON smh.sequence_mailbox_id = sm.id
                LEFT JOIN sequence_mail_alias_settings smas ON smas.mailbox_id = smh.sequence_mailbox_id AND smas.sequence_campaign_id = smh.sequence_campaign_id AND smas.sequence_person_id = smh.sequence_person_id
                LEFT JOIN users u ON smh.sent_by = u.id
                WHERE scs.step_type = 'MAIL_AUTO') tmp
            LEFT JOIN sequence_mail_histories smh ON tmp.sequence_campaign_id = smh.sequence_campaign_id
                AND tmp.sequence_person_id = smh.sequence_person_id
                AND tmp.next_sequence_step_id = smh.sequence_step_id
            WHERE tmp.row_num = 1
                AND tmp.deleted_at IS NULL
                AND tmp.sequence_person_status = 'ACTIVE'
                AND tmp.is_sequence_step_active = TRUE
                AND tmp.next_sequence_step_id IS NOT NULL
                AND smh.id IS NULL
        UNION
            SELECT NULL as mail_history_id,
                sp.id AS sequence_contact_id,
                sp.name AS sequence_person_name,
                sc.id AS sequence_campaign_id,
                sc.name AS sequence_campaign_name,
                scs.id AS sequence_step_id,
                scs."order" AS sequence_step_order,
                tmp.id AS sequence_mailbox_id,
                smas.mailbox_alias_id,
                tmp.email AS email_from,
                smt.title,
                smt.content,
                sp.email AS email_to,
                'SCHEDULED'::mailhistorystatus AS status,
                CASE
                    WHEN scs.timing_type = 'IMMEDIATE'::timingtype
                            AND scs.step_type = 'MAIL_AUTO'::steptype
                            AND scs.created_at >= sp.created_at
                            AND scs.created_at >= scp.time_resumed
                            THEN scs.created_at
                    WHEN scs.timing_type = 'SCHEDULED'::timingtype
                            AND scs.step_type = 'MAIL_AUTO'::steptype
                            AND scs.created_at >= sp.created_at
                            AND scs.created_at >= scp.time_resumed
                            THEN scs.created_at + (((scs.schedule_value || ' '::text) || scs.schedule_unit)::interval)
                    WHEN scs.timing_type = 'IMMEDIATE'::timingtype
                            AND scs.step_type = 'MAIL_AUTO'::steptype
                            AND sp.created_at >= scs.created_at
                            AND sp.created_at >= scp.time_resumed
                            THEN sp.created_at
                    WHEN scs.timing_type = 'SCHEDULED'::timingtype
                            AND scs.step_type = 'MAIL_AUTO'::steptype
                            AND sp.created_at >= scs.created_at
                            AND sp.created_at >= scp.time_resumed
                            THEN sp.created_at + (((scs.schedule_value || ' '::text) || scs.schedule_unit)::interval)
                    WHEN scs.timing_type = 'IMMEDIATE'::timingtype
                            AND scs.step_type = 'MAIL_AUTO'::steptype
                            AND scp.time_resumed >= scs.created_at
                            AND scp.time_resumed >= sp.created_at
                            THEN scp.time_resumed
                    WHEN scs.timing_type = 'SCHEDULED'::timingtype
                            AND scs.step_type = 'MAIL_AUTO'::steptype
                            AND scp.time_resumed >= scs.created_at
                            AND scp.time_resumed >= sp.created_at
                            THEN scp.time_resumed + (((scs.schedule_value || ' '::text) || scs.schedule_unit)::interval)
                    ELSE NULL::timestamp WITHOUT TIME ZONE
                END AS sent_at,
                u.id AS sent_by,
                u.name AS sender_name,
                'FIRST'::text AS mail_history_type,
                NULL AS process_status,
                NULL AS thread_id,
                False AS is_reply_to_previous_thread,
                tmp.is_opt_out_message_after_signature as is_include_opt_out_and_signature,
                -- SỬA: Lấy trực tiếp từ mail_history (tmp)
                tmp.email_signature AS email_signature,
                tmp.opt_out_message_after_signature AS opt_out_message
            FROM sequence_campaigns sc
            JOIN users u ON sc.created_by = u.id
            JOIN sequence_contacts sp ON sc.id = sp.sequence_campaign_id AND sp.deleted_at IS NULL
            JOIN sequence_campaign_contacts scp ON scp.sequence_contact_id = sp.id AND scp.sequence_campaign_id = sc.id AND scp.deleted_at IS NULL
            JOIN sequence_campaign_steps scs ON sc.id = scs.sequence_campaign_id
            AND scs."order" = 1 AND scs.deleted_at IS NULL
            JOIN sequence_step_content_templates smt ON scs.content_template_id = smt.id
            LEFT JOIN
            (SELECT sm.user_id,
                    sm.team_id,
                    sm.email,
                    sm.password,
                    sm.host,
                    sm.port,
                    sm.emails_sent_per_day,
                    sm.emails_sent_per_hour,
                    sm.delay_between_emails,
                    sm.email_signature,
                    sm.opt_out_message_after_signature,
                    sm.is_opt_out_message_after_signature,
                    sm.is_open_tracking,
                    sm.is_click_tracking,
                    sm.is_include_one_click_unsubscribe_headers,
                    sm.created_at,
                    sm.created_by,
                    sm.updated_at,
                    sm.updated_by,
                    sm.deleted_at,
                    sm.deleted_by,
                    sm.id,
                    sm.imap_email,
                    sm.imap_password,
                    sm.imap_host,
                    sm.imap_port,
                    sm.google_refresh_token,
                    sm.mailbox_type,
                    row_number() OVER (PARTITION BY sm.user_id
                                        ORDER BY sm.id) AS row_num
            FROM sequence_mailboxes sm) tmp ON tmp.user_id = sc.created_by
            AND tmp.row_num = 1
            LEFT JOIN sequence_mail_alias_settings smas ON smas.mailbox_id = tmp.id AND smas.sequence_campaign_id = sc.id AND smas.sequence_person_id = sp.id
            LEFT JOIN sequence_mail_histories smh ON smh.sequence_campaign_id = sc.id
            AND smh.sequence_person_id = sp.id
            WHERE smh.id IS NULL AND scs.is_active = TRUE AND sc.is_active = TRUE AND scp.status = 'ACTIVE' AND scs.step_type = 'MAIL_AUTO'
    )
    """
    )


def downgrade() -> None:
    pass
