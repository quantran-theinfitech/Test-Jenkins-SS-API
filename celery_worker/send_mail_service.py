# flake8: noqa: E501
import re
import urllib.parse
import uuid
from datetime import datetime, timedelta

from sqlmodel import Session, and_, select, text, update

from app.config import settings
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.campaign_setting import SequenceCampaignSetting
from app.models.sequence.contact import SequenceContact
from app.models.sequence.content_template import (
    ContentType,
    SequenceStepContentTemplate,
)
from app.models.sequence.linkedin_account import LinkedInAccount
from app.models.sequence.mail_history import (
    MAIL_HISTORY_VIEW_NAME,
    AccountOption,
    FailCode,
    MailHistoryProcessStatus,
    MailHistoryStatus,
    SequenceMailHistory,
)
from app.models.sequence.mailbox import MailboxType, SequenceMailbox
from app.models.sequence.step import (
    ScheduleUnit,
    SequenceCampaignStep,
    StepType,
    TimingType,
)
from app.models.sequence.task import SequenceTask, TaskStatus, TaskType
from app.models.sequence.unsubcription import SequenceUnscription
from app.models.team import Team
from app.models.team_credit import ServiceCode
from app.models.user import User
from external.google import GoogleService
from external.mautic.utils import send_email
from utils.check_signature_setting import has_signature
from utils.credit_utils import consume_credit_with_atomic_update, is_enough_credit
from utils.mailbox_utils import get_mail_alias_setting, handle_opt_out_contact
from utils.sequence_schedule import validate_campaign_on_sending_window


def skip_mail_service(db: Session, mail_history_id: int):
    mail_history = db.get(SequenceMailHistory, mail_history_id)
    if not mail_history:
        print(f"No mail history found for id {mail_history_id}")
        return None

    if mail_history.process_status != MailHistoryProcessStatus.PENDING:
        print(f"Mail history {mail_history_id} is not pending")
        return mail_history

    if mail_history.status != MailHistoryStatus.SKIPPED:
        return None
    mail_history.process_status = MailHistoryProcessStatus.SUCCESS
    mail_history.sent_at = datetime.now()
    return mail_history


async def send_mail(db: Session, mail_history_id: int):
    # mail_history = db.get(SequenceMailHistory, mail_history_id)
    mail_history_campaign_contact = db.exec(
        select(SequenceMailHistory, SequenceCampaignContacts)
        .join(
            SequenceCampaignContacts,
            SequenceMailHistory.sequence_contact_id
            == SequenceCampaignContacts.sequence_contact_id,
        )
        .where(SequenceMailHistory.id == mail_history_id)
    ).first()
    if not mail_history_campaign_contact:
        # print(f"No mail history found for id {mail_history_id}")
        return None
    mail_history, campaign_contact = mail_history_campaign_contact
    mailbox = db.get(SequenceMailbox, mail_history.sequence_mailbox_id)

    if mailbox.deleted_at is not None:
        print(f"Mailbox {mail_history.sequence_mailbox_id} is deleted")
        return mail_history

    if mail_history.process_status != MailHistoryProcessStatus.PENDING:
        print(f"Mail history {mail_history_id} is not pending")
        return mail_history

    if mail_history.status != MailHistoryStatus.SCHEDULED:
        print(f"Mail history {mail_history_id} is not scheduled")
        return mail_history

    if not mail_history.to_address:
        print(f"Mail history {mail_history_id} has no email_to")
        mail_history.status = MailHistoryStatus.NOT_SENT
        campaign_contact.status = StatusEnum.NOT_SENT.value
        db.add(campaign_contact)
        mail_history.process_status = MailHistoryProcessStatus.SUCCESS
        mail_history.fail_reason = "No email address found"
        return mail_history

    campaign = db.exec(
        select(SequenceCampaign).where(
            SequenceCampaign.id == mail_history.sequence_campaign_id
        )
    ).first()

    team = db.get(Team, campaign.team_id)
    if not team:
        print(f"Mail history {mail_history_id} not belongs to any team")
        mail_history.status = MailHistoryStatus.NOT_SENT
        mail_history.process_status = MailHistoryProcessStatus.SUCCESS
        campaign_contact.status = StatusEnum.NOT_SENT.value
        mail_history.fail_reason = FailCode.TEAM_NOT_FOUND
        db.add(campaign_contact)
        return mail_history

    if not is_enough_credit(db, team.id, 1, ServiceCode.EMAIL):
        mail_history.status = MailHistoryStatus.NOT_SENT
        mail_history.process_status = MailHistoryProcessStatus.SUCCESS
        campaign_contact.status = StatusEnum.NOT_SENT.value
        mail_history.sent_at = datetime.now()
        db.add(campaign_contact)
        mail_history.fail_reason = FailCode.NOT_ENOUGH_EMAIL_CREDIT

        steps = db.exec(
            select(SequenceCampaignStep).where(
                SequenceCampaignStep.sequence_campaign_id == campaign.id
            )
        ).all()
        for step in steps:
            if (
                step.step_type == StepType.MAIL_AUTO
                or step.step_type == StepType.MAIL_MANUAL
            ):
                step.is_active = False

        db.commit()

        return mail_history

    mail_template = db.exec(
        select(SequenceStepContentTemplate)
        .join(
            SequenceCampaignStep,
            SequenceCampaignStep.content_template_id == SequenceStepContentTemplate.id,
        )
        .where(
            SequenceCampaignStep.id == mail_history.sequence_step_id,
            SequenceStepContentTemplate.content_type == ContentType.MAIL,
        )
    ).first()

    # campaign_person = db.exec(
    #     select(SequenceCampaignContacts).where(
    #         SequenceCampaignContacts.sequence_contact_id
    #         == mail_history.sequence_contact_id,
    #     )
    # ).first()

    if campaign_contact.status == StatusEnum.FINISH.value:
        mail_history.status = MailHistoryStatus.SKIPPED
        mail_history.process_status = MailHistoryProcessStatus.SUCCESS
        print(f"Contact {campaign_contact.sequence_contact_id} already finished")
        return mail_history

    if campaign_contact.status == StatusEnum.PAUSE.value:
        mail_history.process_status = MailHistoryProcessStatus.PERSON_PAUSED
        return mail_history

    # Handle get mailbox & mail alias
    if not mailbox:
        mailbox = db.exec(
            select(SequenceMailbox)
            .where(
                SequenceMailbox.created_by == campaign.created_by,
                SequenceMailbox.deleted_at.is_(None),
            )
            .order_by(SequenceMailbox.id.asc())
        ).first()

    if not mailbox:
        print(f"No mailbox found for id {mail_history.sequence_mailbox_id}")
        mail_history.process_status = MailHistoryProcessStatus.MAILBOX_NOT_FOUND
        mail_history.status = MailHistoryStatus.FAILED
        mail_history.fail_reason = "No mailbox found"
        campaign_contact.status = StatusEnum.NOT_SENT.value
        db.add(campaign_contact)
        return mail_history

    email_from = mailbox.email

    send_as = None
    mail_alias_id = None

    result = get_mail_alias_setting(
        db,
        mail_history.sequence_campaign_id,
        mail_history.sequence_step_id,
        mail_history.sequence_contact_id,
    )

    if result:
        mailbox, mail_alias = result
        if mailbox:
            email_from = mailbox.email

        if mail_alias:
            send_as = mail_alias.alias_email
            email_from = mail_alias.alias_email
            mail_alias_id = mail_alias.id

    if not mailbox:
        print(f"No mailbox found for id {mail_history.sequence_mailbox_id}")
        mail_history.process_status = MailHistoryProcessStatus.MAILBOX_NOT_FOUND
        mail_history.status = MailHistoryStatus.NOT_SENT
        mail_history.fail_reason = FailCode.EMAIL_NOT_FOUND
        campaign_contact.status = StatusEnum.NOT_SENT.value
        db.add(campaign_contact)
        return mail_history

    # Handle unscription
    unscription = db.exec(
        select(SequenceUnscription).where(
            SequenceUnscription.email_to == mail_history.to_address,
            SequenceUnscription.email_from == email_from,
        )
    ).first()
    if unscription:
        print(f"EMAIL {mail_history.to_address} has unscribe to email {email_from}")
        mail_history.process_status = MailHistoryProcessStatus.SUCCESS
        mail_history.status = MailHistoryStatus.OPT_OUT
        handle_opt_out_contact(db, mail_history)
        return mail_history

    # parse token in content
    person = db.get(SequenceContact, mail_history.sequence_contact_id)
    if not mail_history.content:
        mail_history.content = ""

    mail_history.content = parse_mail_content(mail_history.content, person)

    tracking_token = str(uuid.uuid4())
    trigger_url = f"{settings.APP_URL}/v1/sequence/mail_histories/open?tracking_token={tracking_token}"
    tracking_pixel = f"<img height='1' width='1' src='{trigger_url}' alt='' />"
    content = mail_history.content + tracking_pixel

    # kiểm tra is_include_opt_out_and_signature, nếu là true thì kiểm tra tiếp mailbox có cho phép gửi opt_out không
    if mail_history.is_include_opt_out_and_signature:
        if has_signature(mailbox.email_signature):
            signature = f"<br>{mailbox.email_signature}"
            content = content + signature
        if (
            mailbox.is_opt_out_message_after_signature
            and mailbox.opt_out_message_after_signature
        ):
            encoded_email_from = urllib.parse.quote(email_from)
            encoded_email_to = urllib.parse.quote(mail_history.to_address)
            opt_out_link = f"{settings.FE_URL}/unsubscribe?tracking_token={tracking_token}&sending_email={encoded_email_from}&receiving_email={encoded_email_to}"
            pattern = r"<%(.*?)%>"
            match = re.search(pattern, mailbox.opt_out_message_after_signature)
            replaced_text = None
            if match is not None:
                replaced_text = re.sub(
                    pattern,
                    f'<a href="{opt_out_link}"> {match.group(1)} </a>',
                    mailbox.opt_out_message_after_signature,
                )
            else:
                replaced_text = f'<a href="{opt_out_link}"> {mailbox.opt_out_message_after_signature} </a>'
            opt_out_message = f"<p>{replaced_text}</p>"
            content = content + opt_out_message
    setting = db.exec(
        select(SequenceCampaignSetting).where(
            SequenceCampaignSetting.sequence_campaign_id
            == mail_history.sequence_campaign_id
        )
    ).first()
    cc = []
    bcc = []
    if setting:
        cc = setting.cc_list if setting.cc_list is not None else []
        bcc = setting.bcc_list if setting.bcc_list is not None else []

    try:
        if mailbox.mailbox_type == MailboxType.SMTP:
            res = await send_email(
                mailbox,
                mail_history.title,
                content,
                mail_history.to_address,
                mail_history.thread_id,
                cc,
                bcc,
            )
            if not mail_history.thread_id:
                mail_history.thread_id = res["Message-ID"]
        if mailbox.mailbox_type == MailboxType.GOOGLE_API:
            google_service = GoogleService()
            res = google_service.send_email(
                mail_history.to_address,
                mail_history.title,
                content,
                mailbox.google_refresh_token,
                mail_history.thread_id,
                send_as,
                cc,
                bcc,
            )
            if not res["success"]:
                raise res["detail"]
            if not mail_history.thread_id:
                mail_history.thread_id = res["thread_id"]
        with db.begin(nested=True):
            consumed = consume_credit_with_atomic_update(
                db, team.id, 1, ServiceCode.EMAIL
            )
        if not consumed:
            mail_history.status = MailHistoryStatus.NOT_SENT
            mail_history.process_status = MailHistoryProcessStatus.SUCCESS
            mail_history.sent_at = datetime.now()
            mail_history.fail_reason = FailCode.NOT_ENOUGH_EMAIL_CREDIT
            campaign_contact.status = StatusEnum.NOT_SENT.value
            db.add(campaign_contact)
            steps = db.exec(
                select(SequenceCampaignStep).where(
                    SequenceCampaignStep.sequence_campaign_id == campaign.id
                )
            ).all()
            for step in steps:
                if (
                    step.step_type == StepType.MAIL_AUTO
                    or step.step_type == StepType.MAIL_MANUAL
                ):
                    step.is_active = False

            db.commit()
            return mail_history
        mail_history.sequence_mailbox_id = mailbox.id
        mail_history.mailbox_alias_id = mail_alias_id
        mail_history.status = MailHistoryStatus.SENT
        mail_history.process_status = MailHistoryProcessStatus.SUCCESS
        mail_history.sent_at = datetime.now()
        mail_history.sent_by = mailbox.created_by

    except Exception as e:
        print(f"Event trigger error: {str(e)}")
        mail_history.process_status = MailHistoryProcessStatus.FAILED
        mail_history.status = MailHistoryStatus.FAILED
        mail_history.sent_at = datetime.now()
        campaign_contact.status = StatusEnum.PAUSE.value
        db.add(campaign_contact)
        mail_history.fail_reason = FailCode.UNKNOWN_ERROR
    mail_history.tracking_token = tracking_token
    return mail_history


EMAIL_TOKEN_MAPPING = {
    "email": "email",
    "name": "name",
}


def parse_mail_content(content: str, person: SequenceContact):
    for token, field in EMAIL_TOKEN_MAPPING.items():
        if not getattr(person, field):
            continue
        content = re.sub(f"{{{{{token}}}}}", getattr(person, field), content)
    return content


def handle_next_step(db: Session, mail_history: SequenceMailHistory):
    print(f"HANDLE NEXT STEP for mail history {mail_history.id}")
    if mail_history.status not in (MailHistoryStatus.SENT, MailHistoryStatus.SKIPPED):
        return
    current_step = db.get(SequenceCampaignStep, mail_history.sequence_step_id)
    if not current_step:
        return
    contact = db.get(SequenceContact, mail_history.sequence_contact_id)
    if not contact:
        return
    campaign_contact = db.exec(
        select(SequenceCampaignContacts).where(
            SequenceCampaignContacts.sequence_contact_id
            == mail_history.sequence_contact_id
        )
    ).first()
    if not campaign_contact or campaign_contact.status == StatusEnum.FINISH.value:
        return
    campaign = db.get(SequenceCampaign, mail_history.sequence_campaign_id)
    if not campaign:
        return
    team = db.exec(
        select(Team)
        .join(User, User.team_id == Team.id)
        .where(User.id == mail_history.sent_by)
    ).first()
    if not team:
        mail_history.status = MailHistoryStatus.FAILED
        mail_history.process_status = MailHistoryProcessStatus.SUCCESS
        campaign_contact.status = StatusEnum.NOT_SENT.value
        db.add(campaign_contact)
        mail_history.fail_reason = FailCode.TEAM_NOT_FOUND
        return mail_history
    # Left join to exclude step that has been sent
    next_step = db.exec(
        select(SequenceCampaignStep)
        .join(
            SequenceMailHistory,
            and_(
                SequenceCampaignStep.sequence_campaign_id
                == SequenceMailHistory.sequence_campaign_id,
                SequenceCampaignStep.id == SequenceMailHistory.sequence_step_id,
                SequenceMailHistory.sequence_contact_id == contact.id,
            ),
            isouter=True,
        )
        .where(
            SequenceCampaignStep.sequence_campaign_id
            == mail_history.sequence_campaign_id,
            SequenceCampaignStep.order > current_step.order,
            SequenceCampaignStep.deleted_at.is_(None),
            SequenceMailHistory.id.is_(None),
        )
        .order_by(SequenceCampaignStep.order.asc())
    ).first()

    # no next step -> finish campaign
    if not next_step:
        print(f"PERSON {contact.id} finish for campaign {campaign.id}")
        db.exec(
            update(SequenceCampaignContacts)
            .where(
                SequenceCampaignContacts.sequence_contact_id == contact.id,
                SequenceCampaignContacts.sequence_campaign_id == campaign.id,
            )
            .values(status=StatusEnum.FINISH.value)
        )
        return

    # update sequence person next step value
    contact.current_step = next_step.order
    db.add(contact)
    # next step is manual mail -> create task
    if next_step.step_type == StepType.MAIL_MANUAL:
        print(
            f"ADD TASK FOR person {mail_history.sequence_contact_id} campaign {campaign.id}"
        )
        due_date = get_due_date(next_step)
        valid, schedule = validate_campaign_on_sending_window(
            db, next_step.sequence_campaign_id, due_date
        )
        if not valid:
            if schedule:
                due_date = schedule
        task = SequenceTask(
            team_id=campaign.team_id,
            user_id=campaign.created_by,
            sequence_campaign_id=campaign.id,
            sequence_step_id=next_step.id,
            task_type=TaskType.EMAIL,
            sequence_person_id=mail_history.sequence_contact_id,
            sequence_linkedin_account_id=mail_history.sequence_linkedin_account_id,
            account_option=mail_history.account_option,
            due_date=due_date,
            priority=next_step.priority,
            status=TaskStatus.SCHEDULED,
            created_at=datetime.now(),
            created_by=campaign.created_by,
        )
        db.add(task)
    elif next_step.step_type == StepType.MAIL_AUTO:
        mailbox = db.exec(
            select(SequenceMailbox)
            .where(
                SequenceMailbox.created_by == campaign.created_by,
                SequenceMailbox.deleted_at.is_(None),
            )
            .order_by(SequenceMailbox.id.asc())
        ).first()
        email_from = None
        if mailbox:
            email_from = mailbox.email

        result = get_mail_alias_setting(
            db,
            mail_history.sequence_campaign_id,
            next_step.id,
            mail_history.sequence_contact_id,
        )
        mail_alias = None
        if result:
            mailbox, mail_alias = result
            email_from = mailbox.email
            if mail_alias:
                email_from = mail_alias.alias_email

        # Handle unscription
        unscription = db.exec(
            select(SequenceUnscription).where(
                SequenceUnscription.email_to == contact.email,
                SequenceUnscription.email_from == email_from,
                SequenceUnscription.email_from.isnot(None),
            )
        ).first()
        if unscription:
            template = db.get(
                SequenceStepContentTemplate, next_step.content_template_id
            )
            next_step_mail_history = SequenceMailHistory(
                sequence_mailbox_id=mailbox.id if mailbox else None,
                sequence_campaign_id=campaign.id,
                sequence_contact_id=contact.id,
                sequence_step_id=next_step.id,
                mailbox_alias_id=mail_alias.id if mail_alias else None,
                status=MailHistoryStatus.OPT_OUT,
                title=template.title,
                content=template.content,
                to_address=contact.email,
                sent_at=datetime.now(),
                sent_by=mail_history.sent_by,
                process_status=MailHistoryProcessStatus.SUCCESS,
                is_include_opt_out_and_signature=mail_history.is_include_opt_out_and_signature,
            )
            handle_opt_out_contact(db, mail_history)
            mail_history.next_sequence_step_id = next_step.id
            db.add(mail_history)
            db.add(next_step_mail_history)
            return
    mail_history.next_sequence_step_id = next_step.id
    db.add(mail_history)
    db.flush()
    next_step_mail_history = db.exec(
        text(
            f"""
            SELECT * FROM {MAIL_HISTORY_VIEW_NAME}
            WHERE sequence_step_id = :sequence_step_id
            AND sequence_contact_id = :sequence_contact_id
            AND sequence_campaign_id = :sequence_campaign_id
            """
        ),
        params={
            "sequence_step_id": next_step.id,
            "sequence_contact_id": contact.id,
            "sequence_campaign_id": campaign.id,
        },
    ).first()
    if not next_step_mail_history:
        return
    next_step_mail_history = dict(next_step_mail_history)
    mail_steps = [StepType.MAIL_AUTO, StepType.MAIL_MANUAL]
    step_type_groups = (
        mail_steps
        if next_step.step_type in mail_steps
        else [
            StepType.LINKEDIN_CONNECTION_REQUEST,
            StepType.LINKEDIN_AUTO_MESSAGE,
            StepType.LINKEDIN_VIEW_PROFILE,
        ]
    )
    latest_mail_history = db.exec(
        select(SequenceMailHistory)
        .join(
            SequenceCampaignStep,
            SequenceMailHistory.sequence_step_id == SequenceCampaignStep.id,
        )
        .where(
            SequenceMailHistory.sequence_campaign_id == campaign.id,
            SequenceMailHistory.sequence_contact_id == mail_history.sequence_contact_id,
            SequenceCampaignStep.step_type.in_(step_type_groups),
            SequenceCampaignStep.deleted_at.is_(None),
            SequenceMailHistory.account_option != AccountOption.MANUAL,
        )
        .order_by(SequenceCampaignStep.order.desc())
    ).first()
    if latest_mail_history:
        next_step_mail_history[
            "sequence_mailbox_id"
        ] = latest_mail_history.sequence_mailbox_id
        next_step_mail_history[
            "mailbox_alias_id"
        ] = latest_mail_history.mailbox_alias_id
        next_step_mail_history["to_address"] = latest_mail_history.to_address
        next_step_mail_history[
            "sequence_linkedin_account_id"
        ] = latest_mail_history.sequence_linkedin_account_id
    else:
        if next_step.step_type in mail_steps:
            mailbox = db.exec(
                select(SequenceMailbox)
                .where(
                    SequenceMailbox.created_by == campaign.created_by,
                    SequenceMailbox.deleted_at.is_(None),
                )
                .order_by(SequenceMailbox.id.asc())
            ).first()
            email_from = None
            if mailbox:
                email_from = mailbox.email

            result = get_mail_alias_setting(
                db,
                mail_history.sequence_campaign_id,
                next_step.id,
                mail_history.sequence_contact_id,
            )
            mail_alias = None
            if result:
                mailbox, mail_alias = result
                email_from = mailbox.email
                if mail_alias:
                    email_from = mail_alias.alias_email
            next_step_mail_history["sequence_mailbox_id"] = (
                mailbox.id if mailbox else None
            )
            next_step_mail_history["mailbox_alias_id"] = (
                mail_alias.id if mail_alias else None
            )
            next_step_mail_history["to_address"] = contact.email
            next_step_mail_history["sequence_linkedin_account_id"] = None
        else:
            linkedin_account = db.exec(
                select(LinkedInAccount)
                .where(
                    LinkedInAccount.created_by == campaign.created_by,
                    LinkedInAccount.deleted_at.is_(None),
                )
                .order_by(LinkedInAccount.is_default.desc(), LinkedInAccount.id.asc())
            ).first()
            next_step_mail_history["sequence_linkedin_account_id"] = (
                linkedin_account.id if linkedin_account else None
            )
            next_step_mail_history["to_address"] = contact.linkedin_url
            next_step_mail_history["sequence_mailbox_id"] = None
            next_step_mail_history["mailbox_alias_id"] = None
    db.add(SequenceMailHistory(**next_step_mail_history))
    db.flush()


def get_due_date(step: SequenceCampaignStep):
    if step.timing_type == TimingType.SCHEDULED:
        delayed = None
        if step.schedule_unit == ScheduleUnit.DAYS:
            delayed = timedelta(days=step.schedule_value)
        if step.schedule_unit == ScheduleUnit.HOURS:
            delayed = timedelta(hours=step.schedule_value)
        if step.schedule_unit == ScheduleUnit.MINUTES:
            delayed = timedelta(minutes=step.schedule_value)

        return datetime.now() + delayed
    return datetime.now()
