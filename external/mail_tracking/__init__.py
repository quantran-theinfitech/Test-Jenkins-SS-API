from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlmodel import Session, or_, select

from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.mail_history import (
    MailHistoryBounceType,
    MailHistoryStatus,
    SequenceMailHistory,
)
from app.models.sequence.mailbox import MailboxType, SequenceMailbox
from external.google import GoogleService
from external.imap import IMAPService
from external.mautic import LoggingDecorator

from .utils import update_bounced_mail, update_replied_mail


class MailTrackingService(LoggingDecorator):
    @classmethod
    def exclude_logging(cls):
        return ["__init__", "get_mail_history"]

    def __init__(self):
        pass

    def get_mail_history(
        self,
        db: Session,
        condition: List,
        oldest_check_time: datetime,
    ) -> List[Tuple[SequenceCampaign, SequenceMailHistory, SequenceMailbox]]:
        query = (
            select(SequenceCampaign, SequenceMailHistory, SequenceMailbox)
            .join(
                SequenceMailbox,
                SequenceMailHistory.sequence_mailbox_id == SequenceMailbox.id,
            )
            .join(
                SequenceCampaign,
                SequenceCampaign.id == SequenceMailHistory.sequence_campaign_id,
            )
            .where(
                SequenceCampaign.deleted_at.is_(None),
                SequenceMailHistory.created_at >= oldest_check_time,
                SequenceMailHistory.deleted_at.is_(None),
                *condition,
            )
            .order_by(
                SequenceCampaign.id,
                SequenceMailbox.id,
                SequenceMailHistory.sequence_mailbox_id,
                SequenceMailHistory.created_at.asc(),
            )
        )
        return db.exec(query).all()

    def bounced_tracking(
        self,
        # sequence_campaign_id: int,
        different_time_since_last_check: timedelta,
        db: Session,
        maximum_check_interval: timedelta = timedelta(weeks=2),
    ):
        now = datetime.now()
        oldest_check_time = now - maximum_check_interval
        last_check_time = now - different_time_since_last_check - timedelta(minutes=1)
        mail_history_status = [
            MailHistoryStatus.SENT,
            MailHistoryStatus.BOUNCED,
            MailHistoryStatus.OPENED,
        ]
        condition = [
            SequenceMailHistory.status.in_(mail_history_status),
            or_(
                SequenceMailHistory.bounce_type != MailHistoryBounceType.PERMANENT,
                SequenceMailHistory.bounce_type.is_(None),
            ),
        ]
        response = self.get_mail_history(db, condition, oldest_check_time)
        google = GoogleService()
        imap = IMAPService()
        prev_mailbox_id = None
        bounced_mails = []
        bounced_list = []
        campaign_id = None
        mailbox_id = None
        for campaign, mail_history, mailbox in response:
            if campaign_id != campaign.id:
                print(f"Checking bounced mail in sequence campaign {campaign.id}")
                campaign_id = campaign.id
            if mailbox_id != mailbox.id:
                # print(f"Checking bounced mail in mailbox {mailbox.id}")
                mailbox_id = mailbox.id
                if mailbox.mailbox_type == MailboxType.GOOGLE_API:
                    if prev_mailbox_id != mailbox.id:
                        prev_mailbox_id = mailbox.id
                        bounced_list = google.check_bounced_email(
                            mailbox.google_refresh_token, last_check_time
                        )
                # For SMTP
                if mailbox.mailbox_type == MailboxType.SMTP:
                    if prev_mailbox_id != mailbox.id:
                        prev_mailbox_id = mailbox.id
                        bounced_list = imap.check_bounced_email(
                            mailbox.imap_host,
                            mailbox.imap_port,
                            mailbox.imap_email,
                            mailbox.imap_password,
                            last_check_time,
                        )
            # print(f"Checking bounced mail in mail id: {mail_history.id}")
            for bounced_mail in bounced_list:
                if mail_history.thread_id == bounced_mail.message_id:
                    mail_history = update_bounced_mail(
                        db,
                        mail_history,
                        bounced_mail.bounce_code,
                        bounced_mail.diagnostic_code,
                        now,
                    )
                    bounced_mails.append(mail_history)
            mail_history.updated_at = now
        db.commit()
        bounced_mail_ids = []
        for mail_history in bounced_mails:
            db.refresh(mail_history)
            bounced_mail_ids.append(mail_history.id)
        return bounced_mail_ids

    def replied_tracking(
        self,
        db: Session,
        maximum_check_interval: timedelta = timedelta(weeks=2),
        sequence_campaign_ids: Optional[List[int]] = None,
    ):
        condition = [
            SequenceMailHistory.status.in_(
                [MailHistoryStatus.SENT, MailHistoryStatus.OPENED]
            ),
        ]
        if sequence_campaign_ids:
            condition.append(
                SequenceMailHistory.sequence_campaign_id.in_(sequence_campaign_ids)
            )
        now = datetime.now()
        oldest_check_time = now - maximum_check_interval
        response = self.get_mail_history(db, condition, oldest_check_time)
        google = GoogleService()
        imap = IMAPService()
        replied_mails = []
        replied_mail_ids = []
        campaign_id = None
        for campaign, mail_history, mailbox in response:
            if campaign_id != campaign.id:
                print(f"Checking replied mail in sequence campaign {campaign.id}")
                campaign_id = campaign.id
            # print(f"Checking replied mail in mail id: {mail_history.id}")
            is_replied = False
            # For Google API
            if mailbox.mailbox_type == MailboxType.GOOGLE_API:
                if mail_history.thread_id:
                    is_replied = google.check_replied_email(
                        mail_history.to_address,
                        mail_history.thread_id,
                        mailbox.google_refresh_token,
                    )
            # For SMTP
            if mailbox.mailbox_type == MailboxType.SMTP:
                if mail_history.thread_id:
                    is_replied = imap.check_replied_email(
                        mail_history.thread_id,
                        mail_history.to_address,
                        mailbox.imap_host,
                        mailbox.imap_port,
                        mailbox.imap_email,
                        mailbox.imap_password,
                    )
            if is_replied:
                print(f"Replied mail: {is_replied}")
                replied_mails.append(mail_history)
            mail_history.updated_at = now
        replied_mails = update_replied_mail(db, replied_mails, now)
        db.commit()
        for rep_mail in replied_mails:
            db.refresh(rep_mail)
            replied_mail_ids.append(rep_mail.id)
        return replied_mail_ids
