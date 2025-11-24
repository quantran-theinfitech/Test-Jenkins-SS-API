# flake8: noqa: E501
from fastapi import HTTPException
from sqlmodel import Session, select, text

from app.api.v1.schemas.sequence.linkedin_activities import (
    LinkedInActivityActionRequest,
    RescheduleLinkedInActivityRequest,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.mail_histories.handle_schedule_time import (
    handle_schedule_time,
)
from app.api.v1.services.sequences.mail_histories.update_mail_history_service import (
    convert_to_utc_time,
)
from app.api.v1.services.sequences.mail_histories.verify_campaign_permisstion_service import (
    verify_campaign_permission,
)
from app.models import team
from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.contact import SequenceContact
from app.models.sequence.content_template import SequenceStepContentTemplate
from app.models.sequence.linkedin_account import LinkedInAccount
from app.models.sequence.linkedin_activities import LinkedinHistoryStatus
from app.models.sequence.mail_history import (
    MAIL_HISTORY_VIEW_NAME,
    MailHistoryProcessStatus,
    MailHistoryStatus,
    SequenceMailHistory,
)
from app.models.sequence.step import SequenceCampaignStep
from app.models.team import Team
from app.models.user import User


def get_linkedin_activity(
    db: Session, linkedin_activity_request: LinkedInActivityActionRequest
):
    result = db.exec(
        select(SequenceMailHistory, SequenceContact).join(
            SequenceContact,
            SequenceContact.id == SequenceMailHistory.sequence_contact_id,
        )
        .where(
            SequenceMailHistory.sequence_campaign_id
            == linkedin_activity_request.campaign_id,
            SequenceMailHistory.sequence_contact_id
            == linkedin_activity_request.contact_id,
            SequenceMailHistory.sequence_step_id == linkedin_activity_request.step_id,
            SequenceMailHistory.deleted_at.is_(None),
        )
    ).first()
    if not result:
        return None
    linkedin_activity, contact = result
    linkedin_account_id = None
    team = db.exec(
        select(Team)
        .join(User, User.team_id == Team.id)
        .where(User.id == linkedin_activity.sent_by)
    ).first()
    if not team:
        linkedin_activity.fail_reason = "Team Not Found"
        linkedin_activity.status = MailHistoryStatus.FAILED
        linkedin_activity.process_status = MailHistoryProcessStatus.SUCCESS
        db.add(linkedin_activity)
        db.commit()
        return linkedin_activity
    current_linkedin_account_id = db.exec(
        select(LinkedInAccount.id).where(
            LinkedInAccount.deleted_at.is_(None),
            LinkedInAccount.team_id == team.id,
            LinkedInAccount.id == linkedin_activity.sequence_linkedin_account_id,
        )
    ).first()
    if not current_linkedin_account_id:
        default_linkedin_account_id = db.exec(
            select(LinkedInAccount.id).where(
                LinkedInAccount.is_default.is_(True),
                LinkedInAccount.deleted_at.is_(None),
                LinkedInAccount.team_id == team.id,
            )
        ).first()
        if default_linkedin_account_id:
            linkedin_account_id = default_linkedin_account_id
    else:
        linkedin_account_id = current_linkedin_account_id
    linkedin_activity.sequence_linkedin_account_id = linkedin_account_id
    linkedin_activity.to_address = contact.linkedin_url
    return linkedin_activity


def get_or_create_new_linkedin_activity(
    db: Session,
    linkedin_activity_request: LinkedInActivityActionRequest,
    current_user: UserBase,
):
    linkedin_activity = get_linkedin_activity(db, linkedin_activity_request)
    if linkedin_activity:
        return linkedin_activity
    params = {
        "sequence_campaign_id": linkedin_activity_request.campaign_id,
        "sequence_contact_id": linkedin_activity_request.contact_id,
        "sequence_step_id": linkedin_activity_request.step_id,
    }
    conditions = [
        "v.sequence_campaign_id = :sequence_campaign_id",
        "v.sequence_contact_id = :sequence_contact_id",
        "v.sequence_step_id = :sequence_step_id",
    ]
    condition_sql = " AND ".join(conditions)
    result = db.execute(
        text(
            f"""
                SELECT v.*
                FROM {MAIL_HISTORY_VIEW_NAME} v
                WHERE {condition_sql}
                """
        ),
        params=params,
    ).first()
    contact = db.get(SequenceContact, linkedin_activity_request.contact_id)
    if not contact:
        raise HTTPException(
            status_code=404,
            detail=f"No contact with id {linkedin_activity_request.contact_id}",
        )

    step = db.get(SequenceCampaignStep, linkedin_activity_request.step_id)
    if not step:
        raise HTTPException(
            status_code=404,
            detail=f"No step with id {linkedin_activity_request.step_id}",
        )
    content_template = db.exec(
        select(SequenceStepContentTemplate)
        .join(
            SequenceCampaignStep,
            SequenceCampaignStep.content_template_id == SequenceStepContentTemplate.id,
        )
        .where(SequenceCampaignStep.id == linkedin_activity_request.step_id)
    ).first()

    # if not content_template:
    #     raise Exception(
    #         f"No content template for step with id {linkedin_activity_request.step_id}"
    #     )
    team = db.exec(
        select(Team)
        .join(User, User.team_id == Team.id)
        .where(User.id == result.sent_by)
    ).first()
    if not team:
        linkedin_activity.fail_reason = "Team Not Found"
        linkedin_activity.status = MailHistoryStatus.FAILED
        linkedin_activity.process_status = MailHistoryProcessStatus.SUCCESS
        db.add(linkedin_activity)
        db.commit()
        return linkedin_activity
    linkedin_account_id = None
    current_linkedin_account_id = db.exec(
        select(LinkedInAccount.id).where(
            LinkedInAccount.deleted_at.is_(None),
            LinkedInAccount.team_id == team.id,
            LinkedInAccount.id == result.sequence_linkedin_account_id,
        )
    ).first()
    if not current_linkedin_account_id:
        default_linkedin_account_id = db.exec(
            select(LinkedInAccount.id).where(
                LinkedInAccount.is_default.is_(True),
                LinkedInAccount.deleted_at.is_(None),
                LinkedInAccount.team_id == team.id,
            )
        ).first()
        if default_linkedin_account_id:
            linkedin_account_id = default_linkedin_account_id
    else:
        linkedin_account_id = current_linkedin_account_id
    new_linkedin_activity = SequenceMailHistory(
        sequence_campaign_id=linkedin_activity_request.campaign_id,
        sequence_contact_id=linkedin_activity_request.contact_id,
        sequence_step_id=linkedin_activity_request.step_id,
        to_address=result.to_address,
        status=MailHistoryStatus.SCHEDULED,
        title=content_template.title if content_template else None,
        content=content_template.content if content_template else None,
        sent_by=current_user.id,
        process_status=None,
        sequence_linkedin_account_id=linkedin_account_id,
        sent_at=result.sent_at,
    )
    db.add(new_linkedin_activity)
    db.flush()
    db.refresh(new_linkedin_activity)
    return new_linkedin_activity


def reschedule_linkedin_activity_service(
    db: Session,
    request: RescheduleLinkedInActivityRequest,
    current_user: UserBase,
):
    result = True  # use to check if all linkedin activities are sent or replied
    try:
        for linkedin_activity_request in request.linkedin_activities:
            verify_campaign_permission(
                db, current_user, linkedin_activity_request.campaign_id
            )

        for linkedin_activity_request in request.linkedin_activities:
            linkedin_activity = get_or_create_new_linkedin_activity(
                db, linkedin_activity_request, current_user
            )

            if linkedin_activity.status not in [
                LinkedinHistoryStatus.SENT,
                LinkedinHistoryStatus.REPLIED,
                LinkedinHistoryStatus.SKIPPED,
                LinkedinHistoryStatus.OPENED,
                LinkedinHistoryStatus.OPT_OUT,
                LinkedinHistoryStatus.BOUNCED,
            ]:
                result = False
                linkedin_activity.status = LinkedinHistoryStatus.SCHEDULED
                schedule_time = handle_schedule_time(
                    request.schedule_type, request.custom_datetime
                )
                schedule_time = convert_to_utc_time(
                    db, schedule_time, linkedin_activity.sequence_campaign_id
                )
                linkedin_activity.process_status = None
                linkedin_activity.sent_at = schedule_time
                linkedin_activity.is_rescheduled = True
                db.add(linkedin_activity)
                # update contact to active when reschedule
                campaign_contact = db.exec(
                    select(SequenceCampaignContacts).where(
                        SequenceCampaignContacts.sequence_contact_id
                        == linkedin_activity.sequence_contact_id,
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
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
