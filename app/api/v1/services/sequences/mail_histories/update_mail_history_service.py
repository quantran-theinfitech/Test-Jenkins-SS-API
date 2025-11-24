from datetime import datetime, timezone

import pytz
from sqlmodel import Session, select, text, tuple_, update

from app.api.v1.schemas.sequence.campaigns import StatusEnum
from app.api.v1.schemas.sequence.mail_histories import (
    ChangeMailboxMailHistoryRequest,
    DeleteMailHistoryRequest,
    MailHistoryActionRequest,
    RescheduleMailHistoryStatusRequest,
    RetryMailHistoryRequest,
    SkipMailHistoryStatusRequest,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.mail_histories.handle_schedule_time import (
    handle_schedule_time,
)
from app.api.v1.services.sequences.mailboxes import listing_mailboxes_service
from app.models import (
    SequenceCampaignContacts,
    SequenceCampaignStep,
    SequenceContact,
    SequenceMailAliasSetting,
    SequenceStepContentTemplate,
)
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.content_template import ContentType
from app.models.sequence.mail_alias_setting import SettingOption
from app.models.sequence.mail_history import (
    MAIL_HISTORY_VIEW_NAME,
    MailHistoryProcessStatus,
    MailHistoryStatus,
    SequenceMailHistory,
)
from app.models.sequence.schedule import SequenceCampaignSchedule
from app.models.sequence.step import StepType, TimingType
from celery_worker import skip_mail
from celery_worker.send_mail_service import get_due_date


def skip_mail_history_service(
    db: Session, request: SkipMailHistoryStatusRequest, current_user: UserBase
):
    result = True
    skip_ids = []

    list_mailboxes = listing_mailboxes_service(db, current_user, 1, 0)
    mail_box_default = next(
        (mailbox for mailbox in list_mailboxes if mailbox.is_default), None
    )
    mail_box_default_id = mail_box_default.id if mail_box_default else None

    list_request = [
        (
            mail_history_request.campaign_id,
            mail_history_request.person_id,
            mail_history_request.step_id,
        )
        for mail_history_request in request.mail_histories
    ]

    tuples = list_request
    records_dict = {}
    if tuples:
        placeholders = []
        params = {}
        for i, (c, p, s) in enumerate(tuples):
            placeholders.append(f"(:c{i}, :p{i}, :s{i})")
            params[f"c{i}"] = c
            params[f"p{i}"] = p
            params[f"s{i}"] = s

        values_clause = ", ".join(placeholders)
        query = f"""
        SELECT v.*
        FROM {MAIL_HISTORY_VIEW_NAME} v
        WHERE (v.sequence_campaign_id, v.sequence_contact_id, v.sequence_step_id)
            IN (VALUES {values_clause})
        """
        records = db.exec(text(query), params=params).all()
        for record in records:
            key = (
                record["sequence_campaign_id"],
                record["sequence_contact_id"],
                record["sequence_step_id"],
            )
            records_dict[key] = record

    for mail_history_request in request.mail_histories:
        mail_history = get_or_create_new_mail_history(db, mail_history_request)
        if mail_history.status not in [
            MailHistoryStatus.SENT,
            MailHistoryStatus.OPENED,
            MailHistoryStatus.REPLIED,
            MailHistoryStatus.SKIPPED,
            MailHistoryStatus.OPT_OUT,
            MailHistoryStatus.BOUNCED,
        ]:
            result = False
            mail_history.sent_by = current_user.id
            mail_history.status = MailHistoryStatus.SKIPPED
            mail_history.process_status = MailHistoryProcessStatus.PENDING

            if mail_history.sequence_mailbox_id is None:
                key = (
                    mail_history_request.campaign_id,
                    mail_history_request.person_id,
                    mail_history_request.step_id,
                )
                if key in records_dict:
                    record = records_dict[key]
                    if record["sequence_mailbox_id"] is not None:
                        mail_history.sequence_mailbox_id = record["sequence_mailbox_id"]
                    else:
                        mail_history.sequence_mailbox_id = mail_box_default_id
                else:
                    mail_history.sequence_mailbox_id = mail_box_default_id

            db.add(mail_history)
            db.flush()
            db.refresh(mail_history)
            skip_ids.append(mail_history.id)

    db.commit()

    for mail_history_id in skip_ids:
        skip_mail.apply_async((mail_history_id,))
    return result


def change_mailbox_service(
    db: Session, request: ChangeMailboxMailHistoryRequest, current_user: UserBase
):
    result = True  # use to check if all mail histories are sent or opt-out
    for mail_history_request in request.mail_histories:
        mail_history = get_mail_history(db, mail_history_request)
        if not mail_history:
            params = {
                "sequence_campaign_id": mail_history_request.campaign_id,
                "sequence_contact_id": mail_history_request.person_id,
                "sequence_step_id": mail_history_request.step_id,
            }
            conditions = [
                "v.sequence_campaign_id = :sequence_campaign_id",
                "v.sequence_contact_id = :sequence_contact_id",
                "v.sequence_step_id = :sequence_step_id",
            ]
            condition_sql = " AND ".join(conditions)
            mail_history = db.execute(
                text(
                    f"""
                        SELECT v.*
                        FROM {MAIL_HISTORY_VIEW_NAME} v
                        WHERE {condition_sql}
                        """
                ),
                params=params,
            ).first()
            mail_history = SequenceMailHistory(
                sequence_contact_id=mail_history_request.person_id,
                sequence_campaign_id=mail_history_request.campaign_id,
                sequence_mailbox_id=request.mailbox_id,
                sequence_mailbox_alias_id=request.mailbox_alias_id,
                sequence_step_id=mail_history_request.step_id,
                title=mail_history.title,
                content=mail_history.content,
                to_address=mail_history.to_address,
                status=mail_history.status,
                sent_at=mail_history.sent_at,
                sent_by=current_user.id,
            )
        if mail_history and mail_history.status not in [
            MailHistoryStatus.SENT,
            MailHistoryStatus.OPT_OUT,
            MailHistoryStatus.SKIPPED,
            MailHistoryStatus.REPLIED,
            MailHistoryStatus.OPENED,
            MailHistoryStatus.BOUNCED,
        ]:
            if result:
                result = False
            mail_history.sequence_mailbox_id = (
                request.mailbox_id if request.mailbox_id else None
            )
            mail_history.mailbox_alias_id = (
                request.mailbox_alias_id if request.mailbox_alias_id else None
            )
        db.add(mail_history)

        mail_alias_setting = SequenceMailAliasSetting(
            mailbox_id=request.mailbox_id,
            mailbox_alias_id=request.mailbox_alias_id,
            setting_option=SettingOption.STEP,
            sequence_campaign_id=mail_history_request.campaign_id,
            sequence_person_id=mail_history_request.person_id,
            sequence_step_id=mail_history_request.step_id,
        )
        if request.is_change_subsequent_steps:
            subsequent_mail_alias_setting = SequenceMailAliasSetting(
                mailbox_id=request.mailbox_id,
                mailbox_alias_id=request.mailbox_alias_id,
                setting_option=SettingOption.CONTACT,
                sequence_person_id=mail_history_request.person_id,
                sequence_campaign_id=mail_history_request.campaign_id,
            )
            db.add(subsequent_mail_alias_setting)
        db.add(mail_alias_setting)

    db.commit()
    return result


def delete_mail_history_service(
    db: Session,
    request: DeleteMailHistoryRequest,
):
    for mail_history_request in request.mail_histories:
        mail_history = get_or_create_new_mail_history(db, mail_history_request)
        mail_history.deleted_at = datetime.now()
        db.add(mail_history)
        if mail_history.status == MailHistoryStatus.SCHEDULED:
            person = db.exec(
                select(SequenceCampaignContacts).where(
                    SequenceCampaignContacts.sequence_contact_id
                    == mail_history.sequence_contact_id
                )
            ).first()
            person.status = StatusEnum.FINISH
            person.reason = "Mail history deleted"
            db.add(person)

    db.commit()
    return True


def retry_mail_history_service(
    db: Session,
    request: RetryMailHistoryRequest,
    current_user: UserBase,
):
    list_mailboxes = listing_mailboxes_service(db, current_user, 1, 0)
    mail_box_default = next(
        (mailbox for mailbox in list_mailboxes if mailbox.is_default), None
    )
    if mail_box_default:
        mail_box_default_id = mail_box_default.id
    else:
        mail_box_default_id = None
    list_request = [
        (
            mail_history_request.campaign_id,
            mail_history_request.person_id,
            mail_history_request.step_id,
        )
        for mail_history_request in request.mail_histories
    ]

    tuples = list_request

    if not tuples:
        records = []
    else:
        placeholders = []
        params = {}
        for i, (c, p, s) in enumerate(tuples):
            placeholders.append(f"(:c{i}, :p{i}, :s{i})")
            params[f"c{i}"] = c
            params[f"p{i}"] = p
            params[f"s{i}"] = s

        values_clause = ", ".join(placeholders)
        query = f"""
        SELECT v.*
        FROM {MAIL_HISTORY_VIEW_NAME} v
        WHERE (v.sequence_campaign_id, v.sequence_contact_id, v.sequence_step_id)
            IN (VALUES {values_clause})
        """
        records = db.exec(text(query), params=params).all()

    result = True
    index = -1
    for mail_history_request in request.mail_histories:
        index += 1
        mail_history = get_or_create_new_mail_history(db, mail_history_request)
        if not mail_history:
            continue
        template = db.exec(
            select(SequenceStepContentTemplate)
            .join(
                SequenceCampaignStep,
                SequenceCampaignStep.content_template_id
                == SequenceStepContentTemplate.id,
            )
            .where(SequenceCampaignStep.id == mail_history.sequence_step_id)
        ).first()
        if mail_history.status in [
            MailHistoryStatus.SCHEDULED,
            # MailHistoryStatus.FAILED,
            MailHistoryStatus.NOT_SENT,
        ]:
            result = False
            mail_history.process_status = None
            mail_history.fail_reason = None
            mail_history.status = MailHistoryStatus.SCHEDULED
            mail_history.sent_at = compute_retry_sent_at(db, mail_history)
            mail_history.content = template.content
            mail_history.title = template.title
            mail_history.sequence_mailbox_id = (
                records[index]["sequence_mailbox_id"]
                if records[index]["sequence_mailbox_id"] is not None
                else mail_box_default_id
            )
            mail_history.sent_by = records[index]["sent_by"]
            mail_history.opt_out_message = records[index]["opt_out_message"]
            mail_history.is_include_opt_out_and_signature = records[index][
                "is_include_opt_out_and_signature"
            ]

            db.add(mail_history)
            db.flush()
            db.refresh(mail_history)
    active_person_list = [
        (mail_request.campaign_id, mail_request.person_id)
        for mail_request in request.mail_histories
    ]
    db.exec(
        update(SequenceCampaignContacts)
        .where(
            tuple_(
                SequenceCampaignContacts.sequence_campaign_id,
                SequenceCampaignContacts.sequence_contact_id,
            ).in_(active_person_list)
        )
        .values(status=StatusEnum.ACTIVE)
    )
    db.commit()
    return result


def compute_retry_sent_at(db: Session, mail_history: SequenceMailHistory) -> datetime:
    """Compute sent_at for a retried mail according to the same
    rules as the view 6977c87e51b2.

    The calculation considers step timing, activation time,
    schedule offset, the previous sent_at,
    and the contact's time_resumed. The result is converted to
    the campaign's timezone (UTC output).
    """
    step: SequenceCampaignStep = db.get(
        SequenceCampaignStep, mail_history.sequence_step_id
    )
    if not step:
        return datetime.now(timezone.utc)

    # Only apply rules for MAIL_AUTO; for others fall back to now
    if step.step_type != StepType.MAIL_AUTO:
        return datetime.now(timezone.utc)

    # Gather context
    sequence_step_activated_at = step.activated_at
    timing_type = step.timing_type

    # Use current time as base for retry calculations
    now_utc = datetime.now(timezone.utc)
    campaign_contact = db.exec(
        select(SequenceCampaignContacts).where(
            SequenceCampaignContacts.sequence_campaign_id
            == mail_history.sequence_campaign_id,
            SequenceCampaignContacts.sequence_contact_id
            == mail_history.sequence_contact_id,
        )
    ).first()
    sequence_person_time_resumed = getattr(campaign_contact, "time_resumed", None)

    # Normalize tz to UTC-aware
    def to_aware(dt: datetime) -> datetime:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    sequence_step_activated_at = to_aware(sequence_step_activated_at)
    sequence_person_time_resumed = to_aware(sequence_person_time_resumed)

    computed: datetime = None

    if (
        timing_type == TimingType.IMMEDIATE
        and step.step_type == StepType.MAIL_AUTO
        and (
            sequence_step_activated_at is not None
            and sequence_step_activated_at >= now_utc
            and (
                sequence_person_time_resumed is None
                or sequence_step_activated_at >= sequence_person_time_resumed
            )
        )
    ):
        computed = sequence_step_activated_at
    elif (
        timing_type == TimingType.SCHEDULED
        and step.step_type == StepType.MAIL_AUTO
        and (
            sequence_step_activated_at is not None
            and sequence_step_activated_at >= now_utc
            and (
                sequence_person_time_resumed is None
                or sequence_step_activated_at >= sequence_person_time_resumed
            )
        )
    ):
        # Schedule relative to now, but not earlier than activation time
        candidate = get_due_date(step)
        candidate = to_aware(candidate)
        computed = (
            candidate
            if candidate >= sequence_step_activated_at
            else sequence_step_activated_at
        )
    elif (
        timing_type == TimingType.SCHEDULED
        and step.step_type == StepType.MAIL_AUTO
        and (
            sequence_step_activated_at is None or now_utc >= sequence_step_activated_at
        )
        and (
            sequence_person_time_resumed is None
            or now_utc >= sequence_person_time_resumed
        )
    ):
        # For retry: schedule relative to now, reuse get_due_date(step)
        candidate = get_due_date(step)
        computed = to_aware(candidate)
    elif (
        timing_type == TimingType.IMMEDIATE
        and step.step_type == StepType.MAIL_AUTO
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
        and step.step_type == StepType.MAIL_AUTO
        and (
            sequence_person_time_resumed is not None
            and sequence_person_time_resumed >= now_utc
        )
        and (
            sequence_step_activated_at is None
            or sequence_person_time_resumed >= sequence_step_activated_at
        )
    ):
        # Schedule relative to now, but not earlier than person's resume time
        candidate = get_due_date(step)
        candidate = to_aware(candidate)
        computed = (
            candidate
            if candidate >= sequence_person_time_resumed
            else sequence_person_time_resumed
        )
    elif (
        timing_type == TimingType.IMMEDIATE
        and step.step_type == StepType.MAIL_AUTO
        and (
            sequence_person_time_resumed is not None
            and sequence_person_time_resumed >= now_utc
        )
        and (
            sequence_step_activated_at is None
            or sequence_person_time_resumed >= sequence_step_activated_at
        )
    ):
        computed = sequence_person_time_resumed

    if computed is None:
        computed = datetime.now(timezone.utc)

    # Convert to campaign timezone then back to UTC for storage
    computed = convert_to_utc_time(db, computed, mail_history.sequence_campaign_id)
    return computed


def convert_to_utc_time(
    db: Session, schedule_time: datetime, campaign_id: int
) -> datetime:
    schedule_id = db.get(SequenceCampaign, campaign_id).schedule_id
    schedule = db.get(SequenceCampaignSchedule, schedule_id)
    tz_name = schedule.time_zone if schedule and schedule.time_zone else "UTC"
    tz = pytz.timezone(tz_name)
    if schedule_time.tzinfo is None:
        local_time = tz.localize(schedule_time)
    else:
        local_time = schedule_time.astimezone(tz)
    return local_time.astimezone(pytz.UTC)


def reschedule_mail_history_service(
    db: Session,
    request: RescheduleMailHistoryStatusRequest,
):
    result = True
    for mail_history_request in request.mail_histories:
        mail_history = get_or_create_new_mail_history(db, mail_history_request)
        if mail_history.status not in [
            MailHistoryStatus.SENT,
            MailHistoryStatus.OPT_OUT,
            MailHistoryStatus.SKIPPED,
            MailHistoryStatus.REPLIED,
            MailHistoryStatus.OPENED,
            MailHistoryStatus.BOUNCED,
        ]:
            result = False
            mail_history.status = MailHistoryStatus.SCHEDULED
            schedule_time = handle_schedule_time(
                request.schedule_type, request.custom_datetime
            )
            schedule_time = convert_to_utc_time(
                db, schedule_time, mail_history.sequence_campaign_id
            )
            mail_history.process_status = None
            mail_history.sent_at = schedule_time
            mail_history.is_rescheduled = True
            db.add(mail_history)
    db.commit()
    return result


def get_mail_history(db: Session, mail_history_request: MailHistoryActionRequest):
    result = db.exec(
        select(SequenceMailHistory, SequenceContact)
        .join(
            SequenceContact,
            SequenceContact.id == SequenceMailHistory.sequence_contact_id,
        )
        .where(
            SequenceMailHistory.sequence_campaign_id
            == mail_history_request.campaign_id,
            SequenceMailHistory.sequence_contact_id == mail_history_request.person_id,
            SequenceMailHistory.sequence_step_id == mail_history_request.step_id,
            SequenceMailHistory.deleted_at.is_(None),
        )
    ).first()
    if not result:
        return None
    mail_history, contact = result
    mail_history.to_address = contact.email
    return mail_history


def get_or_create_new_mail_history(
    db: Session, mail_history_request: MailHistoryActionRequest
):
    mail_history = get_mail_history(db, mail_history_request)
    if mail_history:
        return mail_history

    person = db.get(SequenceContact, mail_history_request.person_id)
    if not person:
        raise Exception(f"No person with id {mail_history_request.person_id}")

    mail_template = db.exec(
        select(SequenceStepContentTemplate)
        .join(
            SequenceCampaignStep,
            SequenceCampaignStep.content_template_id == SequenceStepContentTemplate.id,
            SequenceStepContentTemplate.content_type == ContentType.MAIL,
        )
        .where(SequenceCampaignStep.id == mail_history_request.step_id)
    ).first()
    if not mail_template:
        raise Exception(
            f"No mail template for step with id {mail_history_request.step_id}"
        )

    mail_history = SequenceMailHistory(
        sequence_campaign_id=mail_history_request.campaign_id,
        sequence_contact_id=mail_history_request.person_id,
        sequence_step_id=mail_history_request.step_id,
        title=mail_template.title,
        content=mail_template.content,
        to_address=person.email,
        status=MailHistoryStatus.SCHEDULED,
    )
    db.add(mail_history)
    db.flush()
    db.refresh(mail_history)
    return mail_history
