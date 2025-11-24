from datetime import datetime
from typing import Optional

from sqlmodel import Session, or_, select

from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.contact import SequenceContact
from app.models.sequence.mail_alias import SequenceMailAlias
from app.models.sequence.mail_history import (
    MailHistoryBounceType,
    MailHistoryProcessStatus,
    MailHistoryStatus,
    SequenceMailHistory,
)
from app.models.sequence.mailbox import SequenceMailbox
from app.models.sequence.person_statistics import SequencePersonStatistics
from app.models.sequence.step import SequenceCampaignStep, StepType
from app.models.sequence.unsubcription import SequenceUnscription
from app.models.user import User
from utils.mailbox_utils import get_mail_alias_setting, handle_opt_out_contact


def trigger_open_email_service(
    db: Session, tracking_token: str, current_user: Optional[User] = None
):
    # Người dùng mở -> không tiến hành cập nhật gì person_stats
    if current_user:
        return
    results = db.exec(
        select(SequenceMailHistory, SequencePersonStatistics)
        .join(
            SequencePersonStatistics,
            SequenceMailHistory.sequence_contact_id
            == SequencePersonStatistics.sequence_person_id,
            isouter=True,
        )
        .where(
            SequenceMailHistory.tracking_token == tracking_token,
            SequenceMailHistory.status != MailHistoryStatus.REPLIED,
            or_(
                SequenceMailHistory.status != MailHistoryStatus.BOUNCED,
                SequenceMailHistory.bounce_type != MailHistoryBounceType.PERMANENT,
            ),
        )
    ).first()
    if not results:
        print(
            f"""Mail history with token {tracking_token} not found
            or already been replied/bounced"""
        )
        return
    mail_history, person_stats = results
    if person_stats:
        person_stats.email_last_opened_at = datetime.now()
        person_stats.last_activity = datetime.now()
        person_stats.times_opened = (person_stats.times_opened or 0) + 1
    else:
        person_stats = SequencePersonStatistics(
            sequence_person_id=mail_history.sequence_contact_id,
            email_last_opened_at=datetime.now(),
            last_activity=datetime.now(),
            times_opened=1,
        )
    db.add(person_stats)
    mail_history.status = MailHistoryStatus.OPENED
    mail_history.opened_at = datetime.now()
    db.add(mail_history)
    db.commit()


def unscribe_email_service(db: Session, tracking_token: str):
    mail_history = db.exec(
        select(SequenceMailHistory).where(
            SequenceMailHistory.tracking_token == tracking_token
        )
    ).first()
    if not mail_history:
        print(f"Mail history with token {tracking_token} not found")
        return False
    handle_opt_out_contact(db, mail_history)
    mail_history.status = MailHistoryStatus.OPT_OUT
    mail_history.updated_at = datetime.now()
    db.commit()
    mailbox = db.get(SequenceMailbox, mail_history.sequence_mailbox_id)
    if not mailbox or mailbox.deleted_at:
        return False
    email = mailbox.email
    if mail_history.mailbox_alias_id:
        mail_alias = db.get(SequenceMailAlias, mail_history.mailbox_alias_id)
        if not mail_alias:
            return False
        email = mail_alias.alias_email
    unscription = SequenceUnscription(
        email_from=email, email_to=mail_history.to_address
    )
    db.add(unscription)

    if mail_history.next_sequence_step_id:
        next_step = db.get(SequenceCampaignStep, mail_history.next_sequence_step_id)
        campaign = db.get(SequenceCampaign, mail_history.sequence_campaign_id)
        person = db.get(SequenceContact, mail_history.sequence_contact_id)
        email_from = None
        mail_alias = None
        if next_step and next_step.step_type == StepType.MAIL_AUTO:
            mailbox = db.exec(
                select(SequenceMailbox)
                .where(
                    SequenceMailbox.created_by == campaign.created_by,
                    SequenceMailbox.deleted_at.is_(None),
                )
                .order_by(SequenceMailbox.id.asc())
            ).first()

            if mailbox:
                email_from = mailbox.email

            result = get_mail_alias_setting(
                db,
                mail_history.sequence_campaign_id,
                next_step.id,
                mail_history.sequence_contact_id,
            )
            if result:
                mailbox, mail_alias = result
                email_from = mailbox.email
                if mail_alias:
                    email_from = mail_alias.alias_email

        if email_from == email:
            next_step_mail_history = db.exec(
                select(SequenceMailHistory).where(
                    SequenceMailHistory.sequence_campaign_id
                    == mail_history.sequence_campaign_id,
                    SequenceMailHistory.sequence_contact_id
                    == mail_history.sequence_contact_id,
                    SequenceMailHistory.sequence_step_id
                    == mail_history.next_sequence_step_id,
                    SequenceMailHistory.deleted_at.is_(None),
                )
            ).first()

            if not next_step_mail_history:
                # Handle unscription
                next_step_mail_history = SequenceMailHistory(
                    sequence_mailbox_id=mailbox.id if mailbox else None,
                    sequence_campaign_id=campaign.id,
                    sequence_contact_id=person.id,
                    sequence_step_id=next_step.id,
                    mailbox_alias_id=mail_alias.id if mail_alias else None,
                    to_address=person.email,
                    sent_by=mail_history.sent_by,
                )

            if next_step_mail_history:
                next_step_mail_history.status = MailHistoryStatus.OPT_OUT
                next_step_mail_history.sent_at = datetime.now()
                next_step_mail_history.process_status = MailHistoryProcessStatus.SUCCESS
                handle_opt_out_contact(db, next_step_mail_history)
                db.add(next_step_mail_history)

    db.commit()
    return True
