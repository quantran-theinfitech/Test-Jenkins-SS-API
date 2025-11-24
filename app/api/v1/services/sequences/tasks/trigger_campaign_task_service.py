# flake8: noqa: E501
from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.sequence.tasks import TriggerTaskAction, TriggerTaskRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.mail_histories.handle_schedule_time import (
    handle_schedule_time,
)
from app.models.sequence.contact import SequenceContact
from app.models.sequence.content_template import SequenceStepContentTemplate
from app.models.sequence.mail_alias_setting import (
    SequenceMailAliasSetting,
    SettingOption,
)
from app.models.sequence.mail_history import (
    MailHistoryProcessStatus,
    MailHistoryStatus,
    SequenceMailHistory,
)
from app.models.sequence.mailbox import SequenceMailbox
from app.models.sequence.step import SequenceCampaignStep
from app.models.sequence.task import SequenceTask, TaskStatus
from celery_worker import skip_mail
from utils.check_signature_setting import has_signature


def trigger_task_service(
    db: Session, request: TriggerTaskRequest, current_user: UserBase
):
    result = True  # check if all task is completed or archived
    ids = []
    mailbox = db.exec(
        select(SequenceMailbox)
        .where(
            SequenceMailbox.created_by == current_user.id,
            SequenceMailbox.deleted_at.is_(None),
        )
        .order_by(SequenceMailbox.id.asc())
    ).first()
    if not mailbox and request.action == TriggerTaskAction.START:
        raise NotFoundException("sequence.mailboxNotFound")
    for task_id in request.task_ids:
        task = db.get(SequenceTask, task_id)
        if not task:
            continue
        if task.status not in [TaskStatus.COMPLTETED, TaskStatus.ARCHIVED]:
            result = False
            task.status = TaskStatus.COMPLTETED
            person = db.get(SequenceContact, task.sequence_person_id)
            if not person:
                continue
            mail_history = SequenceMailHistory(
                sequence_campaign_id=task.sequence_campaign_id,
                sequence_contact_id=task.sequence_person_id,
                sequence_step_id=task.sequence_step_id,
                sequence_mailbox_id=mailbox.id if mailbox else None,
                sequence_linkedin_account_id=task.sequence_linkedin_account_id,
                account_option=task.account_option,
                to_address=person.email,
                sent_by=current_user.id,
                is_include_opt_out_and_signature=request.is_include_opt_out_and_signature,
            )
            if request.action == TriggerTaskAction.SKIPPED:
                task.status = TaskStatus.ARCHIVED
                mail_history.status = MailHistoryStatus.SKIPPED
                mail_history.process_status = MailHistoryProcessStatus.PENDING

            if request.action == TriggerTaskAction.START:
                step = db.get(SequenceCampaignStep, task.sequence_step_id)
                if not step:
                    continue
                mail_template = db.get(
                    SequenceStepContentTemplate, step.content_template_id
                )
                if not mail_template:
                    continue
                if mail_template.is_reply_to_previous_thread:
                    prev_mail_history = db.exec(
                        select(SequenceMailHistory).where(
                            SequenceMailHistory.sequence_contact_id
                            == task.sequence_person_id,
                            SequenceMailHistory.next_sequence_step_id
                            == task.sequence_step_id,
                            SequenceMailHistory.deleted_at.is_(None),
                        )
                    ).first()
                    if prev_mail_history:
                        mail_history.thread_id = prev_mail_history.thread_id

                schedule_time = handle_schedule_time(
                    request.schedule_type, request.custom_datetime
                )
                mail_history.status = MailHistoryStatus.SCHEDULED
                mail_history.process_status = None
                mail_history.sent_at = schedule_time
                if request.title:
                    mail_history.title = request.title
                if request.content:
                    mail_history.content = request.content
                # Chọn checkbox gửi opt_out và signature
                if mail_history.is_include_opt_out_and_signature is True:
                    # Có cài đặt opt_out và signature
                    if mailbox.is_opt_out_message_after_signature and has_signature(
                        mailbox.email_signature
                    ):
                        mail_history.email_signature = mailbox.email_signature
                        mail_history.opt_out_message = (
                            mailbox.opt_out_message_after_signature
                        )
                    # Chỉ cài đặt opt_out
                    elif (
                        mailbox.is_opt_out_message_after_signature is True
                        and has_signature(mailbox.email_signature) is False
                    ):
                        mail_history.email_signature = None
                        mail_history.opt_out_message = (
                            mailbox.opt_out_message_after_signature
                        )
                    # Chỉ cài đặt signature
                    elif (
                        mailbox.is_opt_out_message_after_signature is False
                        and has_signature(mailbox.email_signature)
                    ):
                        mail_history.email_signature = mailbox.email_signature
                        mail_history.opt_out_message = None
                    # Không cài đặt cả opt_out và signature
                    else:
                        mail_history.opt_out_message = None
                        mail_history.email_signature = None
                # Không chọn checkbox gửi opt_out và signature
                else:
                    mail_history.opt_out_message = None
                    mail_history.email_signature = None

            db.add(mail_history)
            db.flush()
            db.refresh(mail_history)
            ids.append(mail_history.id)

    if request.action == TriggerTaskAction.START:
        for mail_history_id in ids:
            mail_alias_setting = SequenceMailAliasSetting(
                mailbox_id=request.mailbox_id,
                mailbox_alias_id=request.mailbox_alias_id,
                setting_option=SettingOption.STEP,
                sequence_campaign_id=mail_history.sequence_campaign_id,
                sequence_person_id=mail_history.sequence_contact_id,
                sequence_step_id=mail_history.sequence_step_id,
            )
            db.add(mail_alias_setting)

    db.commit()

    if request.action == TriggerTaskAction.SKIPPED:
        for mail_history_id in ids:
            # Assuming skip_mail is a Celery task
            skip_mail.apply_async((mail_history_id,))
    return result
