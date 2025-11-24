# flake8: noqa: E501
import re
import uuid
from datetime import datetime, timezone
from typing import List

from sqlmodel import Session, select

from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.contact import SequenceContact
from app.models.sequence.content_items import ContentItemsType, SequenceStepContentItem
from app.models.sequence.linkedin_account import LinkedInAccount
from app.models.sequence.mail_history import (
    FailCode,
    MailHistoryProcessStatus,
    MailHistoryStatus,
    SequenceMailHistory,
)
from app.models.sequence.step import (
    FallbackMessageAction,
    SequenceCampaignStep,
    StepType,
)
from app.models.sequence.task import SequenceTask, TaskStatus
from app.models.team import Team
from app.models.team_credit import ServiceCode
from celery_worker.send_mail_service import handle_next_step
from external.s3 import S3Service
from utils.credit_utils import consume_credit_with_atomic_update, is_enough_credit
from utils.unipile import extract_vanity_name_linkedin, retrieve_users, send_message

s3_service = S3Service()

MESSAGE_TOKEN_MAPPING = {
    "name": "name",
    "email": "email",
    "address": "address",
    "role_name": "role_name",
}


def send_linkedin_message_service(db: Session, history_id: int):
    history, campaign_contact = db.exec(
        select(SequenceMailHistory, SequenceCampaignContacts)
        .join(
            SequenceCampaignContacts,
            SequenceMailHistory.sequence_contact_id
            == SequenceCampaignContacts.sequence_contact_id,
        )
        .where(SequenceMailHistory.id == history_id)
    ).first()

    if not history:
        print(f"No history found for id {history_id}")
        return None

    if history.status != MailHistoryStatus.SCHEDULED:
        print(f"History {history_id} is not scheduled")
        return history

    if history.process_status != MailHistoryProcessStatus.PENDING:
        print(f"History {history_id} is not pending")
        return history

    campaign = db.get(SequenceCampaign, history.sequence_campaign_id)

    team = db.get(Team, campaign.team_id)
    if not team:
        print(f"History {history_id} not belongs to any team")
        history.status = MailHistoryStatus.NOT_SENT
        campaign_contact.status = StatusEnum.NOT_SENT.value
        db.add(campaign_contact)
        history.process_status = MailHistoryProcessStatus.SUCCESS
        history.fail_reason = FailCode.TEAM_NOT_FOUND
        return history

    if not is_enough_credit(db, team.id, 1, ServiceCode.LINKEDIN_MSG):
        print(f"History {history_id} not enough credit")
        history.status = MailHistoryStatus.NOT_SENT
        campaign_contact.status = StatusEnum.NOT_SENT.value
        db.add(campaign_contact)
        history.process_status = MailHistoryProcessStatus.SUCCESS
        history.fail_reason = FailCode.NOT_ENOUGH_LINKEDIN_CREDIT

        steps = db.exec(
            select(SequenceCampaignStep).where(
                SequenceCampaignStep.sequence_campaign_id == campaign.id
            )
        ).all()
        for step in steps:
            if (
                step.step_type == StepType.LINKEDIN_AUTO_MESSAGE
                or step.step_type == StepType.LINKEDIN_VIEW_PROFILE
                or step.step_type == StepType.LINKEDIN_CONNECTION_REQUEST
            ):
                step.is_active = False

        db.commit()

        return history

    # campaign_contact = db.exec(
    #     select(SequenceCampaignContacts).where(
    #         SequenceCampaignContacts.sequence_contact_id == history.sequence_contact_id,
    #     )
    # ).first()

    if campaign_contact.status == StatusEnum.FINISH.value:
        print(f"Contact {campaign_contact.sequence_contact_id} already finished")
        history.status = MailHistoryStatus.SKIPPED
        history.process_status = MailHistoryProcessStatus.SUCCESS
        return history

    if campaign_contact.status == StatusEnum.PAUSE.value:
        print(f"Contact {campaign_contact.sequence_contact_id} is paused")
        history.process_status = MailHistoryProcessStatus.PERSON_PAUSED
        return history

    step = db.get(SequenceCampaignStep, history.sequence_step_id)

    messages = db.exec(
        select(SequenceStepContentItem)
        .where(
            SequenceStepContentItem.step_content_template_id
            == step.content_template_id,
        )
        .order_by(SequenceStepContentItem.order.asc())
    ).all()

    # linkedin_account_from = db.exec(
    #     select(LinkedInAccount)
    #     .where(
    #         LinkedInAccount.user_id == campaign.created_by,
    #         LinkedInAccount.deleted_at.is_(None),
    #     )
    #     .order_by(LinkedInAccount.id.asc())
    # ).first()
    if history.sequence_linkedin_account_id:
        linkedin_account_from = db.get(
            LinkedInAccount, history.sequence_linkedin_account_id
        )

    if not linkedin_account_from:
        linkedin_account_from = db.exec(
            select(LinkedInAccount)
            .where(
                LinkedInAccount.team_id == team.id,
                LinkedInAccount.deleted_at.is_(None),
            )
            .order_by(LinkedInAccount.id.asc())
        ).first()

    tracking_token = str(uuid.uuid4())

    if not linkedin_account_from:
        print(f"No linkedin account found for team {team.id}")
        history.status = MailHistoryStatus.NOT_SENT
        history.process_status = MailHistoryProcessStatus.LINKEDIN_ACCOUNT_NOT_FOUND
        campaign_contact.status = StatusEnum.NOT_SENT.value
        db.add(campaign_contact)
        history.fail_reason = FailCode.LINKEDIN_SENDER_NOT_FOUND

        return history

    identifier = extract_vanity_name_linkedin(history.to_address)
    linkedin_account_to = retrieve_users(identifier, linkedin_account_from.account_id)

    if not linkedin_account_to:
        print("To address account id not found")
        history.status = MailHistoryStatus.FAILED
        history.process_status = MailHistoryProcessStatus.FAILED
        history.sent_at = datetime.now()
        campaign_contact.status = StatusEnum.PAUSE.value
        db.add(campaign_contact)
        history.fail_reason = FailCode.UNKNOWN_ERROR

        return history

    if linkedin_account_to.get("type") == "errors/resource_not_found":
        history.status = MailHistoryStatus.FAILED
        history.process_status = MailHistoryProcessStatus.FAILED
        history.sent_at = datetime.now()
        campaign_contact.status = StatusEnum.PAUSE.value
        db.add(campaign_contact)
        history.fail_reason = FailCode.ACCOUNT_RECONNECT_REQUIRED

        return history

    if linkedin_account_to.get("type") == "errors/invalid_recipient":
        history.status = MailHistoryStatus.NOT_SENT
        history.process_status = MailHistoryProcessStatus.LINKEDIN_ACCOUNT_NOT_FOUND
        history.sent_at = datetime.now()
        campaign_contact.status = StatusEnum.NOT_SENT.value
        db.add(campaign_contact)
        history.fail_reason = FailCode.RECIPIENT_LINKEDIN_ACCOUNT_NOT_FOUND

        return history
    provider_id = linkedin_account_to["provider_id"]

    print(f"To address account id: {provider_id}")

    is_inmail = False

    contact = db.exec(
        select(SequenceContact).where(SequenceContact.id == history.sequence_contact_id)
    ).first()

    try:
        is_success, response = _send_message(
            messages,
            linkedin_account_from,
            contact,
            provider_id,
            is_inmail,
        )
        if not is_success and not is_inmail:
            fallback_action = step.fallback_message_action
            if fallback_action == FallbackMessageAction.INMAIL:
                is_success, response = _send_message(
                    messages,
                    linkedin_account_from,
                    contact,
                    provider_id,
                    True,
                )
                is_inmail = True

            elif fallback_action == FallbackMessageAction.SKIP:
                history.status = MailHistoryStatus.SKIPPED
                history.sent_at = datetime.now(timezone.utc)
                history.process_status = MailHistoryProcessStatus.SUCCESS
                history.fail_reason = "Error sending message: {response}"
                handle_next_step(db, history)
                return history

        if not is_success:
            print(f"Error sending message: {response}")
            history.status = MailHistoryStatus.FAILED
            history.process_status = MailHistoryProcessStatus.FAILED
            history.sent_at = datetime.now()
            campaign_contact.status = StatusEnum.PAUSE.value
            campaign_contact.time_resumed = None
            db.add(campaign_contact)
            if response["type"] == "errors/insufficient_credits":
                history.fail_reason = FailCode.INSUFFICIENT_CREDITS
            elif response["type"] == "errors/already_invited_recently":
                history.fail_reason = FailCode.ALREADY_INVITED_RECENTLY
            elif response["type"] == "errors/cannot_resend_yet":
                history.fail_reason = FailCode.CANNOT_RESEND_YET
            elif response["type"] == "errors/cannot_invite_attendee":
                history.fail_reason = FailCode.CANNOT_INVITE_ATTENDEE
            elif response["type"] == "errors/provider_error":
                history.fail_reason = FailCode.PROVIDER_ERROR
            elif response["type"] == "errors/limit_exceeded":
                history.fail_reason = FailCode.LIMIT_EXCEEDED
            else:
                history.fail_reason = FailCode.UNKNOWN_ERROR

            return history
        else:
            with db.begin(nested=True):
                consumed = consume_credit_with_atomic_update(
                    db, team.id, 1, ServiceCode.LINKEDIN_MSG
                )
            if not consumed:
                history.status = MailHistoryStatus.NOT_SENT
                history.process_status = MailHistoryProcessStatus.SUCCESS
                history.sent_at = datetime.now()
                history.fail_reason = FailCode.NOT_ENOUGH_LINKEDIN_CREDIT
                contact.status = StatusEnum.NOT_SENT.value
                db.add(contact)
                steps = db.exec(
                    select(SequenceCampaignStep).where(
                        SequenceCampaignStep.sequence_campaign_id == campaign.id
                    )
                ).all()
                for step in steps:
                    if (
                        step.step_type == StepType.LINKEDIN_CONNECTION_REQUEST
                        or step.step_type == StepType.LINKEDIN_AUTO_MESSAGE
                        or step.step_type == StepType.LINKEDIN_VIEW_PROFILE
                    ):
                        step.is_active = False

                db.commit()
                return history

        history.status = MailHistoryStatus.SENT
        history.process_status = MailHistoryProcessStatus.SUCCESS
        history.sent_at = datetime.now()
        history.sent_by = linkedin_account_from.user_id
        history.sequence_linkedin_account_id = linkedin_account_from.id
        db.add(campaign_contact)
    except Exception as e:
        print(f"Error sending message: {e}")
        history.status = MailHistoryStatus.FAILED
        history.process_status = MailHistoryProcessStatus.FAILED
        history.sent_at = datetime.now()
        campaign_contact.status = StatusEnum.PAUSE.value
        campaign_contact.time_resumed = None
        history.fail_reason = f"Error sending message: {e}"
        db.add(campaign_contact)
    history.tracking_token = tracking_token
    return history


def _send_message(
    messages: List[SequenceStepContentItem],
    linkedin_account_from: LinkedInAccount,
    contact: SequenceContact,
    provider_id: str,
    is_inmail: bool,
):

    files = []
    payload = {
        "attendees_ids": provider_id,
        "account_id": linkedin_account_from.account_id,
    }
    for message in messages:
        if message.type == ContentItemsType.TEXT:
            content = parse_msg_content(message.content, contact)
            payload["text"] = content
        elif (
            message.type == ContentItemsType.IMAGE
            or message.type == ContentItemsType.FILE
        ):
            file_key = message.file_path
            file_content = None
            file_type = None
            if file_key:
                result = s3_service.get_object_bytes(file_key)
                if result:
                    file_content, file_type = result

            if not file_content:
                print(
                    f"""Failed to retrieve file content from S3 with key
                    '{file_key}' for message {message.id}"""
                )
                is_success, response = False, "File content not found in S3"
            else:
                files.append(
                    ("attachments", (message.file_name, file_content, file_type))
                )
    is_success, response = send_message(payload, files, is_inmail)
    return is_success, response


def parse_msg_content(content: str, person: SequenceContact):
    for token, field in MESSAGE_TOKEN_MAPPING.items():
        if token == "role_name":
            value = ".".join(person.role_name) if person.role_name else ""
            content = re.sub(f"{{{{{token}}}}}", value, content)
        else:
            if not getattr(person, field):
                continue
            content = re.sub(f"{{{{{token}}}}}", getattr(person, field), content)
    return content
