from sqlmodel import Session, select, text

from app.api.v1.schemas.sequence.mailboxes import SimpleMailSenderResponse
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.mail_histories.verify_campaign_permisstion_service import (
    verify_campaign_permission,
)
from app.models.sequence.mail_history import MAIL_HISTORY_VIEW_NAME, MailHistoryStatus


def get_filter_mail_sender_service(
    db: Session, current_user: UserBase, campaign_id: int
):
    verify_campaign_permission(db, current_user, campaign_id)
    params = {
        "sequence_campaign_id": campaign_id,
        "exclude_status": MailHistoryStatus.SKIPPED,
    }
    conditions = [
        "v.sequence_campaign_id = :sequence_campaign_id",
        "v.status != :exclude_status",
        "v.to_address IS NOT NULL",
    ]
    condition_sql = " AND ".join(conditions)
    results = db.execute(
        text(
            f"""
                SELECT DISTINCT v.email_from
                FROM {MAIL_HISTORY_VIEW_NAME} v
                JOIN sequence_campaign_steps scs
                ON v.sequence_step_id = scs.id
                WHERE {condition_sql}
                AND scs.step_type IN ('MAIL_AUTO', 'MAIL_MANUAL')
                """
        ),
        params=params,
    ).all()
    data = [
        SimpleMailSenderResponse(id=i + 1, address=result[0])
        for i, result in enumerate(results)
        if result and result[0]
    ]

    return data
