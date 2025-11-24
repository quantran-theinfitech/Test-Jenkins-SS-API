import uuid
from datetime import timedelta

from sqlmodel import Session, select

from app.api.v1.schemas.sequence.campaigns import StatusEnum
from app.config import settings
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_contacts import SequenceCampaignContacts
from app.models.sequence.mail_history import (
    MailHistoryProcessStatus,
    MailHistoryStatus,
    SequenceMailHistory,
)
from app.models.sequence.mailbox import SequenceMailbox
from app.models.sequence.mautic_event_step import SequenceMauticEventStep
from app.models.sequence.mautic_person import SequenceMauticPerson
from app.models.sequence.step import ScheduleUnit, SequenceCampaignStep, TimingType
from celery_worker import skip_mail, trigger_mail
from external.mautic.schema.campaign import MauticTriggerEventRequest


def get_next_step_eta_time(step: SequenceCampaignStep):
    delayed = timedelta(minutes=1)
    if step.timing_type == TimingType.SCHEDULED:
        if step.schedule_unit == ScheduleUnit.DAYS:
            delayed = timedelta(days=step.schedule_value)
        if step.schedule_unit == ScheduleUnit.HOURS:
            delayed = timedelta(hours=step.schedule_value)
        if step.schedule_unit == ScheduleUnit.MINUTES:
            delayed = timedelta(minutes=step.schedule_value)

    return delayed


async def trigger_event_service(
    request: MauticTriggerEventRequest,
    db: Session,
):
    if (
        len(request.source) != 2
        or request.source[0] != "campaign.event"
        or not request.lead.sequence_email
    ):
        return

    mautic_event_id = request.source[1]

    campaign = db.exec(
        select(SequenceCampaign)
        .join(
            SequenceCampaignStep,
            SequenceCampaignStep.sequence_campaign_id == SequenceCampaign.id,
        )
        .join(
            SequenceMauticEventStep,
            SequenceMauticEventStep.sequence_campaign_step_id
            == SequenceCampaignStep.id,
        )
        .where(SequenceMauticEventStep.external_mautic_event_id == mautic_event_id)
    ).first()

    mautic_event = db.exec(
        select(SequenceMauticEventStep).where(
            SequenceMauticEventStep.external_mautic_event_id == mautic_event_id,
        )
    ).first()

    step = db.exec(
        select(SequenceCampaignStep).where(
            SequenceCampaignStep.id == mautic_event.sequence_campaign_step_id
        )
    ).first()

    if not step.is_active:
        print(f"Step {step.id} is not active")
        return

    contact = db.exec(
        select(SequenceMauticPerson).where(
            SequenceMauticPerson.external_mautic_person_id == request.lead.id,
        )
    ).first()

    campaign_person = db.exec(
        select(SequenceCampaignContacts).where(
            SequenceCampaignContacts.sequence_contact_id == contact.sequence_person_id
        )
    ).first()

    if campaign_person.status == StatusEnum.FINISH.value:
        print(f"Person {campaign_person.sequence_contact_id} already finished")
        return

    exists_mail_history = db.exec(
        select(SequenceMailHistory).where(
            SequenceMailHistory.sequence_contact_id == contact.sequence_person_id,
            SequenceMailHistory.sequence_campaign_id == campaign.id,
            SequenceMailHistory.sequence_step_id
            == mautic_event.sequence_campaign_step_id,
        )
    ).first()

    # Get mailbox by team_id
    mailbox = db.exec(
        select(SequenceMailbox)
        .where(
            SequenceMailbox.created_by == campaign.created_by,
            SequenceMailbox.deleted_at.is_(None),
        )
        .order_by(SequenceMailbox.id.asc())
    ).first()

    email = request.lead.sequence_email

    tracking_token = str(uuid.uuid4())
    trigger_url = f"{settings.APP_URL}/v1/sequence/mail_histories/open?tracking_token={tracking_token}"
    content = request.content.replace("{tracking_pixel}", trigger_url)

    if exists_mail_history:
        if exists_mail_history.status == MailHistoryStatus.SENT:
            return
        if (
            exists_mail_history.status == MailHistoryStatus.SKIPPED
            or exists_mail_history.deleted_at is not None
        ):
            exists_mail_history.process_status = MailHistoryProcessStatus.PENDING
            db.add(exists_mail_history)
            db.flush()
            db.commit()
            skip_mail.apply_async((exists_mail_history.id,))
            print(f"Mail history {exists_mail_history.id} has been skipped or deleted")
            return
        
        if exists_mail_history.status == MailHistoryStatus.SCHEDULED:
            exists_mail_history.to_address = email
            exists_mail_history.title = request.subject
            exists_mail_history.content = content
            exists_mail_history.tracking_token = tracking_token
            exists_mail_history.sequence_mailbox_id = mailbox.id if mailbox else None
            exists_mail_history.process_status = MailHistoryProcessStatus.PENDING
            db.add(exists_mail_history)
            db.commit()
            print(f"Mail history {exists_mail_history.id} has been scheduled")
            return

    mail_history = SequenceMailHistory(
        sequence_contact_id=contact.sequence_person_id,
        sequence_campaign_id=campaign.id,
        sequence_step_id=mautic_event.sequence_campaign_step_id,
        to_address=email,
        title=request.subject,
        content=content,
        sequence_mailbox_id=mailbox.id if mailbox else None,
        process_status=MailHistoryProcessStatus.PENDING,
        tracking_token=tracking_token,
    )
    db.add(mail_history)
    db.flush()

    previous_step = db.exec(
        select(SequenceCampaignStep)
        .where(
            SequenceCampaignStep.sequence_campaign_id == campaign.id,
            SequenceCampaignStep.order < step.order,
            SequenceCampaignStep.is_active.is_(True),
        )
        .order_by(SequenceCampaignStep.order.desc())
    ).first()

    if not previous_step:
        db.commit()
        trigger_mail.apply_async((mail_history.id,))
        return

    previous_mail_history = db.exec(
        select(SequenceMailHistory).where(
            SequenceMailHistory.sequence_contact_id == contact.sequence_person_id,
            SequenceMailHistory.sequence_campaign_id == campaign.id,
            SequenceMailHistory.sequence_step_id == previous_step.id,
        )
    ).first()

    if not previous_mail_history:
        db.commit()
        trigger_mail.apply_async((mail_history.id,))
        return

    db.commit()
    eta_step = get_next_step_eta_time(step)

    trigger_mail.apply_async(
        (mail_history.id,), eta=previous_mail_history.sent_at + eta_step
    )
