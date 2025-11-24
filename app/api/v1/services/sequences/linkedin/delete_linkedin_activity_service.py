from datetime import datetime

from sqlmodel import Session, select

from app.api.v1.schemas.sequence.campaigns import StatusEnum
from app.api.v1.schemas.sequence.linkedin_activities import (
    DeleteLinkedInActivityRequest,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.linkedin.reschedule_linkedin_activity_service import (
    get_or_create_new_linkedin_activity,
)
from app.models.sequence.campaign_contacts import SequenceCampaignContacts
from app.models.sequence.linkedin_activities import LinkedinHistoryStatus


def delete_linkedin_activity_service(
    db: Session, 
    request: DeleteLinkedInActivityRequest, 
    current_user: UserBase
):
    for activity_req in request.linkedin_activities:
        linkedin_activity = get_or_create_new_linkedin_activity(
            db, activity_req, current_user
        )
        linkedin_activity.deleted_at = datetime.now()
        db.add(linkedin_activity)
        if linkedin_activity.status == LinkedinHistoryStatus.SCHEDULED:
            contact = db.exec(
                select(SequenceCampaignContacts).where(
                    SequenceCampaignContacts.sequence_contact_id
                    == activity_req.contact_id
                )
            ).first()
            contact.status = StatusEnum.FINISH
            contact.reason = "LinkedIn activity deleted"
            db.add(contact)
    db.commit()
    return True
