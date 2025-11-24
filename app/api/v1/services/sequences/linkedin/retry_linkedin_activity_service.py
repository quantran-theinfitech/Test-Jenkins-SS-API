# flake8: noqa: E501
from datetime import datetime, timezone

from sqlalchemy import tuple_
from sqlmodel import Session, select, update

from app.api.v1.schemas.sequence.linkedin_activities import RetryLinkedInActivityRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.linkedin.reschedule_linkedin_activity_service import (
    get_or_create_new_linkedin_activity,
)
from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.content_template import SequenceStepContentTemplate
from app.models.sequence.linkedin_activities import LinkedinHistoryStatus
from app.models.sequence.mail_history import MailHistoryStatus
from app.models.sequence.step import SequenceCampaignStep, StepType, TimingType
from celery_worker.send_mail_service import get_due_date


def retry_linkedin_activity_service(
    db: Session, request: RetryLinkedInActivityRequest, current_user: UserBase
):
    result = True  # use to check if one of linkedin activities is scheduled or failed
    for activity_req in request.linkedin_activities:
        linkedin_activity = get_or_create_new_linkedin_activity(
            db, activity_req, current_user
        )
        if not linkedin_activity or linkedin_activity.status in [
            LinkedinHistoryStatus.SCHEDULED,
            # LinkedinHistoryStatus.FAILED,
            MailHistoryStatus.NOT_SENT,
        ]:
            result = False
            template = db.exec(
                select(SequenceStepContentTemplate)
                .join(
                    SequenceCampaignStep,
                    SequenceCampaignStep.content_template_id
                    == SequenceStepContentTemplate.id,
                )
                .where(SequenceCampaignStep.id == linkedin_activity.sequence_step_id)
            ).first()
            linkedin_activity.process_status = None
            linkedin_activity.fail_reason = None
            linkedin_activity.status = MailHistoryStatus.SCHEDULED
            linkedin_activity.sent_at = compute_retry_sent_at_linkedin(
                db, linkedin_activity
            )
            linkedin_activity.content = template.content if template else None
            db.add(linkedin_activity)
            db.flush()
            db.refresh(linkedin_activity)
    active_contact_list = [
        (activity_req.campaign_id, activity_req.contact_id)
        for activity_req in request.linkedin_activities
    ]
    db.exec(
        update(SequenceCampaignContacts)
        .where(
            tuple_(
                SequenceCampaignContacts.sequence_campaign_id,
                SequenceCampaignContacts.sequence_contact_id,
            ).in_(active_contact_list)
        )
        .values(status=StatusEnum.ACTIVE)
    )
    db.commit()
    return result


def compute_retry_sent_at_linkedin(db: Session, activity):
    """Compute sent_at for retried LinkedIn activities based on step timing rules.

    Uses now as the base for SCHEDULED intervals (get_due_date(step)) and respects
    step activation time and contact's time_resumed similar to the view logic.
    """
    step: SequenceCampaignStep = db.get(SequenceCampaignStep, activity.sequence_step_id)
    if not step:
        return datetime.now(timezone.utc)

    # Only apply for LinkedIn auto steps
    linkedin_steps = {
        StepType.LINKEDIN_CONNECTION_REQUEST,
        StepType.LINKEDIN_AUTO_MESSAGE,
        StepType.LINKEDIN_VIEW_PROFILE,
    }
    if step.step_type not in linkedin_steps:
        return datetime.now(timezone.utc)

    sequence_step_activated_at = step.activated_at
    timing_type = step.timing_type
    now_utc = datetime.now(timezone.utc)

    campaign_contact = db.exec(
        select(SequenceCampaignContacts).where(
            SequenceCampaignContacts.sequence_campaign_id
            == activity.sequence_campaign_id,
            SequenceCampaignContacts.sequence_contact_id
            == activity.sequence_contact_id,
        )
    ).first()
    sequence_person_time_resumed = getattr(campaign_contact, "time_resumed", None)

    def to_aware(dt):
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    sequence_step_activated_at = to_aware(sequence_step_activated_at)
    sequence_person_time_resumed = to_aware(sequence_person_time_resumed)
    now_utc = to_aware(now_utc)

    computed = None

    if (
        timing_type == TimingType.IMMEDIATE
        and sequence_step_activated_at is not None
        and sequence_step_activated_at >= now_utc
        and (
            sequence_person_time_resumed is None
            or sequence_step_activated_at >= sequence_person_time_resumed
        )
    ):
        computed = sequence_step_activated_at
    elif (
        timing_type == TimingType.SCHEDULED
        and sequence_step_activated_at is not None
        and sequence_step_activated_at >= now_utc
        and (
            sequence_person_time_resumed is None
            or sequence_step_activated_at >= sequence_person_time_resumed
        )
    ):
        candidate = get_due_date(step)
        candidate = to_aware(candidate)
        computed = (
            candidate
            if candidate >= sequence_step_activated_at
            else sequence_step_activated_at
        )
    elif (
        timing_type == TimingType.SCHEDULED
        and (
            sequence_step_activated_at is None or now_utc >= sequence_step_activated_at
        )
        and (
            sequence_person_time_resumed is None
            or now_utc >= sequence_person_time_resumed
        )
    ):
        candidate = get_due_date(step)
        computed = to_aware(candidate)
    elif (
        timing_type == TimingType.IMMEDIATE
        and (
            sequence_step_activated_at is None or now_utc >= sequence_step_activated_at
        )
        and (
            sequence_person_time_resumed is None
            or now_utc >= sequence_person_time_resumed
        )
    ):
        computed = now_utc
    elif (
        timing_type == TimingType.SCHEDULED
        and sequence_person_time_resumed is not None
        and sequence_person_time_resumed >= now_utc
        and (
            sequence_step_activated_at is None
            or sequence_person_time_resumed >= sequence_step_activated_at
        )
    ):
        candidate = get_due_date(step)
        candidate = to_aware(candidate)
        computed = (
            candidate
            if candidate >= sequence_person_time_resumed
            else sequence_person_time_resumed
        )
    elif (
        timing_type == TimingType.IMMEDIATE
        and sequence_person_time_resumed is not None
        and sequence_person_time_resumed >= now_utc
        and (
            sequence_step_activated_at is None
            or sequence_person_time_resumed >= sequence_step_activated_at
        )
    ):
        computed = sequence_person_time_resumed

    if computed is None:
        computed = now_utc

    return computed
