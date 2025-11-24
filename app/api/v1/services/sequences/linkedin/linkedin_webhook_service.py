from datetime import datetime
from fastapi import Request
from app.api.v1.services.sequences.linkedin.retry_linkedin_activity_service import (
    retry_linkedin_activity_service,
)
from sqlmodel import Session, select, update
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_contacts import StatusEnum, SequenceCampaignContacts
from app.models.sequence.linkedin_account import LinkedInAccount, LinkedInAccountStatus
from app.models.sequence.mail_history import SequenceMailHistory
from app.api.v1.schemas.sequence.linkedin_activities import (
    RetryLinkedInActivityRequest,
    LinkedInActivityActionRequest,
)
from sqlalchemy import select, update
from datetime import datetime
from app.api.v1.services.sequences.linkedin.reschedule_linkedin_activity_service import (
    get_linkedin_activity,
)
from app.models.sequence.linkedin_activities import LinkedinHistoryStatus


def pause_linkedin_activity_service(db: Session, request: RetryLinkedInActivityRequest):
    now = datetime.now()
    updated_activities = []

    for activity_req in request.linkedin_activities:
        linkedin_activity = get_linkedin_activity(db, activity_req)
        if linkedin_activity and linkedin_activity.status in [
            LinkedinHistoryStatus.SCHEDULED,
            LinkedinHistoryStatus.BOUNCED,
        ]:
            linkedin_activity.deleted_at = now
            updated_activities.append(linkedin_activity)

    if updated_activities:
        db.add_all(updated_activities)
        db.commit()


async def linkedin_webhook_service(
    request: Request,
    db: Session,
):
    data = await request.json()
    account_id = data["AccountStatus"]["account_id"]
    account_type = data["AccountStatus"]["account_type"]
    message = data["AccountStatus"]["message"]

    account_linkedin = (
        db.query(LinkedInAccount)
        .filter(
            LinkedInAccount.account_id == account_id,
            LinkedInAccount.account_type == account_type,
            LinkedInAccount.deleted_at.is_(None),
        )
        .first()
    )

    if not account_linkedin:
        return {"message": "success"}

    campaigns_active = (
        db.query(SequenceCampaign)
        .filter(
            SequenceCampaign.team_id == account_linkedin.team_id,
            SequenceCampaign.deleted_at.is_(None),
            SequenceCampaign.is_active.is_(True),
        )
        .all()
    )

    sequence_ids = [c.id for c in campaigns_active]

    if not sequence_ids:
        all_mail_not_sent = []
    else:
        sequence_contact_ids_active_and_paused = (
            db.execute(
                select(SequenceCampaignContacts.sequence_contact_id).where(
                    SequenceCampaignContacts.sequence_campaign_id.in_(sequence_ids),
                    SequenceCampaignContacts.deleted_at.is_(None),
                    SequenceCampaignContacts.status.in_(
                        [
                            StatusEnum.ACTIVE.value,
                            StatusEnum.PAUSE.value,
                            StatusEnum.NOT_SENT.value,
                        ]
                    ),
                )
            )
            .scalars()
            .all()
        )

        mail_histories = (
            db.query(SequenceMailHistory)
            .filter(
                SequenceMailHistory.sequence_contact_id.in_(
                    sequence_contact_ids_active_and_paused
                ),
                SequenceMailHistory.deleted_at.is_(None),
                SequenceMailHistory.status.in_(["SCHEDULED", "FAILED", "BOUNCED"]),
            )
            .all()
        )

        all_mail_not_sent = [
            LinkedInActivityActionRequest(
                campaign_id=mh.sequence_campaign_id,
                contact_id=mh.sequence_contact_id,
                step_id=mh.sequence_step_id,
            )
            for mh in mail_histories
        ]

    if message in [LinkedInAccountStatus.CREDENTIALS, LinkedInAccountStatus.OK]:
        account_linkedin.status = message
        account_linkedin.updated_at = datetime.now()
        db.commit()

        if account_linkedin.is_default and sequence_ids:
            new_status = (
                StatusEnum.PAUSE.value
                if message == LinkedInAccountStatus.CREDENTIALS
                else StatusEnum.ACTIVE.value
            )

            if new_status == StatusEnum.ACTIVE.value and all_mail_not_sent:
                retry_linkedin_activity_service(
                    db,
                    RetryLinkedInActivityRequest(linkedin_activities=all_mail_not_sent),
                    None,
                )

            if new_status == StatusEnum.PAUSE.value and all_mail_not_sent:
                pause_linkedin_activity_service(
                    db,
                    RetryLinkedInActivityRequest(linkedin_activities=all_mail_not_sent),
                )

            db.execute(
                update(SequenceCampaignContacts)
                .where(
                    SequenceCampaignContacts.sequence_campaign_id.in_(sequence_ids),
                    SequenceCampaignContacts.deleted_at.is_(None),
                    (
                        SequenceCampaignContacts.status.in_(
                            [StatusEnum.ACTIVE.value, StatusEnum.NOT_SENT.value]
                        )
                        if new_status == StatusEnum.PAUSE.value
                        else SequenceCampaignContacts.status.in_(
                            [StatusEnum.PAUSE.value, StatusEnum.NOT_SENT.value]
                        )
                    ),
                )
                .values(
                    status=new_status,
                    time_resumed=(
                        datetime.now()
                        if new_status == StatusEnum.ACTIVE.value
                        else None
                    ),
                )
            )
            db.commit()

        return {"message": "success"}

    return {"message": "success"}
