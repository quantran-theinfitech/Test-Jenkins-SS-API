# flake8: noqa: E501
from datetime import datetime

from sqlmodel import Session

from app.api.v1.schemas.sequence.linkedin_activities import SkipLinkedInActivityRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.linkedin.reschedule_linkedin_activity_service import (
    get_or_create_new_linkedin_activity,
)
from app.models.sequence.linkedin_activities import LinkedinHistoryStatus
from app.models.sequence.mail_history import MailHistoryStatus
from app.models.sequence.step import SequenceCampaignStep
from celery_worker.send_mail_service import handle_next_step


def skip_linkedin_activity_service(
    db: Session, request: SkipLinkedInActivityRequest, current_user: UserBase
):
    result = True  # use to check if one of linkedin activities is scheduled or failed
    for activity_req in request.linkedin_activities:
        linkedin_activity = get_or_create_new_linkedin_activity(
            db, activity_req, current_user
        )
        if linkedin_activity.status in [
            MailHistoryStatus.SCHEDULED,
            MailHistoryStatus.FAILED,
            MailHistoryStatus.NOT_SENT,
        ]:
            result = False
            current_step = db.get(SequenceCampaignStep, activity_req.step_id)
            if not current_step:
                continue

            linkedin_activity.status = MailHistoryStatus.SKIPPED
            linkedin_activity.sent_at = datetime.now()
            db.add(linkedin_activity)
            handle_next_step(db, linkedin_activity)

    db.commit()
    return result
