# flake8: noqa: E501
from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.sequence.linkedin_activities import (
    ChangeLinkedInAccountHistoryRequest,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.linkedin.reschedule_linkedin_activity_service import (
    get_or_create_new_linkedin_activity,
)
from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.mail_history import MailHistoryStatus


def update_activity_executor_service(
    db: Session, request: ChangeLinkedInAccountHistoryRequest, current_user: UserBase
):
    result = True  # use to check if all linkedin activities are not scheduled or failed
    for activity_req in request.linkedin_activities:
        activity = get_or_create_new_linkedin_activity(db, activity_req, current_user)
        if not activity:
            raise NotFoundException(detail="activty.NotFound")
        if activity.status in (
            MailHistoryStatus.SCHEDULED,
            MailHistoryStatus.FAILED,
            MailHistoryStatus.NOT_SENT,
        ):
            result = False
            activity.sequence_linkedin_account_id = request.linkedin_account_id
            activity.account_option = request.account_option
            db.add(activity)
            # update contact to active when change sender
            campaign_contact = db.exec(
                select(SequenceCampaignContacts).where(
                    SequenceCampaignContacts.sequence_contact_id
                    == activity.sequence_contact_id,
                    SequenceCampaignContacts.deleted_at.is_(None),
                    SequenceCampaignContacts.status.in_(
                        [StatusEnum.NOT_SENT, StatusEnum.BOUNCED]
                    ),
                )
            ).first()
            if campaign_contact:
                campaign_contact.status = StatusEnum.ACTIVE
                db.add(campaign_contact)
    db.commit()
    return result
