import uuid
from datetime import datetime

from sqlmodel import Session, select

from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.linkedin_account import LinkedInAccount
from app.models.sequence.mail_history import (
    FailCode,
    MailHistoryProcessStatus,
    MailHistoryStatus,
    SequenceMailHistory,
)
from app.models.sequence.step import SequenceCampaignStep, StepType
from app.models.team import Team
from app.models.team_credit import ServiceCode
from utils.credit_utils import consume_credit_with_atomic_update, is_enough_credit
from utils.unipile import extract_vanity_name_linkedin, retrieve_users


def view_linkedin_profile_service(db: Session, history_id: int):
    history, contact = db.exec(
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
        contact.status = StatusEnum.NOT_SENT.value
        db.add(contact)
        history.process_status = MailHistoryProcessStatus.SUCCESS
        history.fail_reason = FailCode.TEAM_NOT_FOUND
        return history

    if not is_enough_credit(db, team.id, 1, ServiceCode.LINKEDIN_MSG):
        print(f"History {history_id} not enough credit")
        history.status = MailHistoryStatus.NOT_SENT
        contact.status = StatusEnum.NOT_SENT.value
        history.sent_at = datetime.now()
        db.add(contact)
        history.process_status = MailHistoryProcessStatus.SUCCESS
        history.fail_reason = FailCode.NOT_ENOUGH_LINKEDIN_CREDIT

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

    # campaign_contact = db.exec(
    #     select(SequenceCampaignContacts).where(
    #         SequenceCampaignContacts.sequence_contact_id
    #         == history.sequence_contact_id,
    #     )
    # ).first()

    if contact.status == StatusEnum.FINISH.value:
        print(f"Contact {contact.sequence_contact_id} already finished")
        history.status = MailHistoryStatus.SKIPPED
        history.process_status = MailHistoryProcessStatus.SUCCESS
        return history

    if contact.status == StatusEnum.PAUSE.value:
        print(f"Contact {contact.sequence_contact_id} is paused")
        history.process_status = MailHistoryProcessStatus.PERSON_PAUSED
        return history

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
        history.status = MailHistoryStatus.FAILED
        history.process_status = MailHistoryProcessStatus.LINKEDIN_ACCOUNT_NOT_FOUND
        history.fail_reason = FailCode.LINKEDIN_SENDER_NOT_FOUND
        contact.status = StatusEnum.NOT_SENT.value
        db.add(contact)
        return history

    identifier = extract_vanity_name_linkedin(history.to_address)
    # try:
    #     retrieve_users(
    #         user_identifier=identifier,
    #         account_id=linkedin_account_from.account_id,
    #         notify=True,
    #     )
    # except Exception as e:
    #     print(f"Error retrieving users: {e}")
    #     history.status = MailHistoryStatus.FAILED
    #     history.process_status = MailHistoryProcessStatus.FAILED
    #     contact.status = StatusEnum.NOT_SENT.value
    #     history.fail_reason = f"Recipient LinkedIn account not found"
    #     db.add(contact)
    #     return history
    linkedin_account_to = retrieve_users(
        user_identifier=identifier,
        account_id=linkedin_account_from.account_id,
        notify=True,
    )
    if not linkedin_account_to:
        print("To address account id not found")
        history.status = MailHistoryStatus.FAILED
        history.process_status = MailHistoryProcessStatus.FAILED
        history.sent_at = datetime.now()
        contact.status = StatusEnum.PAUSE.value
        db.add(contact)
        history.fail_reason = FailCode.UNKNOWN_ERROR

        return history

    if linkedin_account_to.get("type") == "errors/resource_not_found":
        print("To address account id not found")
        history.status = MailHistoryStatus.FAILED
        history.process_status = MailHistoryProcessStatus.FAILED
        history.sent_at = datetime.now()
        contact.status = StatusEnum.PAUSE.value
        db.add(contact)
        history.fail_reason = FailCode.ACCOUNT_RECONNECT_REQUIRED

        return history

    if linkedin_account_to.get("type") == "errors/invalid_recipient":
        history.status = MailHistoryStatus.NOT_SENT
        history.process_status = MailHistoryProcessStatus.LINKEDIN_ACCOUNT_NOT_FOUND
        history.sent_at = datetime.now()
        contact.status = StatusEnum.NOT_SENT.value
        db.add(contact)
        history.fail_reason = FailCode.RECIPIENT_LINKEDIN_ACCOUNT_NOT_FOUND
        return history
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
    history.sent_by = linkedin_account_from.created_by
    history.tracking_token = tracking_token
    db.add(history)
    db.add(contact)

    return history
