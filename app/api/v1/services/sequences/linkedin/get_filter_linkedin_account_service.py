from sqlmodel import Session, select, text

from app.api.v1.schemas.sequence.linkedin_account import (
    ListingAllAccountItem,
    SimpleLinkedinSenderResponse,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.mail_histories.verify_campaign_permisstion_service import (
    verify_campaign_permission,
)
from app.models.sequence.linkedin_account import LinkedInAccount
from app.models.sequence.mail_history import MAIL_HISTORY_VIEW_NAME, MailHistoryStatus


def get_filter_linkedin_account_service(
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
    ]
    condition_sql = " AND ".join(conditions)
    account_ids_result = db.execute(
        text(
            f"""
                SELECT v.sequence_linkedin_account_id
                FROM {MAIL_HISTORY_VIEW_NAME} v
                JOIN sequence_campaign_steps scs
                ON v.sequence_step_id = scs.id
                WHERE {condition_sql}
                AND scs.step_type IN ('LINKEDIN_AUTO_MESSAGE', 'LINKEDIN_CONNECTION_REQUEST', 'LINKEDIN_VIEW_PROFILE')
                """
        ),
        params=params,
    ).all()

    if not account_ids_result:
        return []

    account_ids = [row[0] for row in account_ids_result]

    linkedin_accounts = db.exec(
        select(LinkedInAccount)
        .distinct(LinkedInAccount.public_identifier)
        .where(
            LinkedInAccount.id.in_(account_ids),
        )
    ).all()

    if not linkedin_accounts:
        return []
    data = [
        SimpleLinkedinSenderResponse(
            id=i + 1,
            account_name=linkedin_account.account_name,
            public_identifier=linkedin_account.public_identifier,
        )
        for i, linkedin_account in enumerate(linkedin_accounts)
    ]
    return data
