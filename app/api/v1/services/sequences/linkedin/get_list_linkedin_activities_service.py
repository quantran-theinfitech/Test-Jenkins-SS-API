# flake8: noqa: E501
from sqlalchemy import bindparam
from sqlmodel import Session, select, text

from app.api.v1.schemas.sequence.linkedin_activities import (
    LinkedInActivityBase,
    LinkedInActivityStatus,
    LinkedInActivityType,
    ListingLinkedInActivityRequest,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.media import media_service
from app.api.v1.services.sequences.mail_histories.verify_campaign_permisstion_service import (
    verify_campaign_permission,
)
from app.models.sequence.linkedin_account import LinkedInAccount
from app.models.sequence.linkedin_activities import (
    LinkedinHistoryProcessStatus,
    LinkedinHistoryStatus,
)
from app.models.sequence.mail_history import MAIL_HISTORY_VIEW_NAME, MailHistoryStatus
from app.models.sequence.step import StepType
from app.models.user import User


def list_linkedin_histories_service(
    db: Session,
    sequence_campaign_id: int,
    current_user: UserBase,
    request: ListingLinkedInActivityRequest,
):
    params = {
        "sequence_campaign_id": sequence_campaign_id,
        "exclude_status": MailHistoryStatus.SKIPPED.value,
    }

    conditions = [
        "v.sequence_campaign_id = :sequence_campaign_id",
        "v.status != :exclude_status",
    ]

    step_type_filters = []
    if request.types:
        if LinkedInActivityType.LINKEDIN_AUTO_MESSAGE in request.types:
            step_type_filters.append("scs.step_type = 'LINKEDIN_AUTO_MESSAGE'")
        if LinkedInActivityType.LINKEDIN_CONNECTION_REQUEST in request.types:
            step_type_filters.append("scs.step_type = 'LINKEDIN_CONNECTION_REQUEST'")
        if LinkedInActivityType.LINKEDIN_VIEW_PROFILE in request.types:
            step_type_filters.append("scs.step_type = 'LINKEDIN_VIEW_PROFILE'")
    if step_type_filters:
        conditions.append("(" + " OR ".join(step_type_filters) + ")")

    status_filters = []
    if request.statuses:
        if LinkedInActivityStatus.SCHEDULED in request.statuses:
            status_filters.append("v.status = 'SCHEDULED'")
        if LinkedInActivityStatus.BOUNCED in request.statuses:
            status_filters.append("v.status = 'BOUNCED'")
        if LinkedInActivityStatus.SPAM_BLOCKED in request.statuses:
            status_filters.append("v.status = 'OPT_OUT'")
        if LinkedInActivityStatus.DELIVERED in request.statuses:
            status_filters.append("v.status IN ('SENT', 'OPENED', 'REPLIED')")
        if LinkedInActivityStatus.NOT_SENT in request.statuses:
            status_filters.append("v.status IN ('DRAFT', 'NOT_SENT')")
        if LinkedInActivityStatus.FAILED in request.statuses:
            status_filters.append("v.status = 'FAILED'")
        if LinkedInActivityStatus.PAUSED in request.statuses:
            status_filters.append("v.process_status = 'PERSON_PAUSED'")

    if status_filters:
        conditions.append("(" + " OR ".join(status_filters) + ")")

    if request.keyword:
        params["keyword"] = f"%{request.keyword}%"
        conditions.append(
            "(v.sequence_person_name ILIKE :keyword "
            "OR regexp_replace(v.content, E'[\\r\\n]+', ' ', 'g') ILIKE :keyword)"
        )

    if request.step_ids:
        params["step_ids"] = request.step_ids
        conditions.append("v.sequence_step_id = ANY(:step_ids)")

    if request.linkedin_user_id:
        params["linkedin_user_id"] = request.linkedin_user_id
        conditions.append("v.sequence_linkedin_account_id = :linkedin_user_id")

    if request.linkedin_senders:
        account_ids = db.exec(
            select(LinkedInAccount.id).where(
                LinkedInAccount.public_identifier.in_(request.linkedin_senders)
            )
        ).all()
        params["linkedin_senders"] = account_ids
        conditions.append("v.sequence_linkedin_account_id = ANY(:linkedin_senders)")

    if request.order is not None:
        order_by = f"v.sent_at {request.order.value}"
    else:
        order_by = "CASE WHEN v.status = 'SCHEDULED' THEN 0 ELSE 1 END, v.sent_at DESC"

    where_clause = " AND ".join(conditions)

    result = (
        db.execute(
            text(
                f"""
                SELECT v.*, smt.*, scs.step_type,
                       v.title AS title,
                       v.content AS message,
                       smh.created_at AS created_at,
                       smh.updated_at AS updated_at
                FROM {MAIL_HISTORY_VIEW_NAME} v
                JOIN sequence_campaign_steps scs
                  ON scs.id = v.sequence_step_id
                LEFT JOIN sequence_mail_histories smh
                  ON smh.id = v.mail_history_id
                LEFT JOIN sequence_step_content_templates smt
                  ON scs.content_template_id = smt.id
                WHERE {where_clause}
                ORDER BY {order_by}
                LIMIT {request.per_page}
                OFFSET {(request.page - 1) * request.per_page}
                """
            ),
            params=params,
        )
        .mappings()
        .all()
    )

    response = []
    for linkedin_activity in result:
        linkedin_account = db.get(
            LinkedInAccount, linkedin_activity.sequence_linkedin_account_id
        )
        linkedin_activity_res = LinkedInActivityBase(**dict(linkedin_activity))
        user = db.get(User, linkedin_activity_res.sent_by)
        linkedin_activity_res.sender_name = user.name if user else None
        linkedin_activity_res.sender_avatar = (
            media_service.get_presigned_url(user.avatar_path)
            if user.avatar_path
            else None
        )
        response.append(linkedin_activity_res)

    total_result = (
        db.execute(
            text(
                f"""
                SELECT COUNT(*) AS total
                FROM {MAIL_HISTORY_VIEW_NAME} v
                JOIN sequence_campaign_steps scs
                  ON scs.id = v.sequence_step_id
                LEFT JOIN sequence_step_content_templates smt
                  ON scs.content_template_id = smt.id
                WHERE {where_clause}
                """
            ),
            params=params,
        )
        .mappings()
        .first()
    )

    total = total_result["total"] if total_result else 0
    return response, total


def get_linkedin_histories_statistics_service(
    db, sequence_campaign_id, current_user, step_id
):
    verify_campaign_permission(db, current_user, sequence_campaign_id)
    # spam_subtype = [
    #     MailHistoryBounceSubType.SUPPRESSED.value,
    #     MailHistoryBounceSubType.ON_ACCOUNT_SUPPRESSION_LIST.value,
    #     MailHistoryBounceSubType.CONTENT_REJECTED.value,
    #     MailHistoryBounceSubType.ATTACHMENT_REJECTED.value,
    # ]
    params = {
        # "spam_subtype": spam_subtype,
        "sequence_campaign_id": sequence_campaign_id,
        "exclude_status": MailHistoryStatus.SKIPPED.value,
        "exclude_step_type": [StepType.MAIL_AUTO.value, StepType.MAIL_MANUAL.value],
    }
    condition = ""
    if step_id:
        condition += f"AND v.sequence_step_id = {step_id}"
    result = (
        db.exec(
            text(
                f"""SELECT count(*) AS total,
        count(CASE
                    WHEN (
                        v.status = '{MailHistoryStatus.SENT.value}'
                        OR v.status = '{MailHistoryStatus.OPENED.value}'
                        OR v.status = '{MailHistoryStatus.REPLIED.value}'
                    ) THEN 1
                END) AS delivered,
        count(CASE
                    WHEN (
                        v.status = '{MailHistoryStatus.SCHEDULED.value}'
                    ) THEN 1
                END) AS scheduled,
        count(CASE
                    WHEN (
                        v.status IN ('{MailHistoryStatus.DRAFT.value}', '{MailHistoryStatus.NOT_SENT.value}')
                    ) THEN 1
                END) AS not_sent,
        count(CASE
                    WHEN (
                        v.status = '{MailHistoryStatus.FAILED.value}'
                    ) THEN 1
                END) AS failed,
        count(CASE
                    WHEN (
                        v.status = '{MailHistoryStatus.OPT_OUT.value}'
                    ) THEN 1
                END) AS spam_blocked,
        count(CASE
                    WHEN (
                        v.status = '{MailHistoryStatus.BOUNCED.value}'
                    ) THEN 1
                END) AS bounced,
        count(CASE
                    WHEN (
                        v.process_status  = '{LinkedinHistoryProcessStatus.PERSON_PAUSED.value}'
                    ) THEN 1
                END) AS paused
        FROM {MAIL_HISTORY_VIEW_NAME} v
        JOIN sequence_campaign_steps scs
        ON scs.id = v.sequence_step_id
        LEFT JOIN sequence_step_content_templates smt
        ON scs.content_template_id = smt.id
        WHERE
            v.sequence_campaign_id = :sequence_campaign_id
            AND v.status != :exclude_status
            AND scs.step_type NOT IN :exclude_step_type
            {condition}
        """
            ).bindparams(bindparam("exclude_step_type", expanding=True)),
            params=params,
        )
        .mappings()
        .first()
    )
    result = dict(result)
    return result
