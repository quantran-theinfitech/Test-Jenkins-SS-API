from datetime import datetime
from typing import List

from sqlmodel import Session, select, tuple_, update

from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.campaign_setting import SequenceCampaignSetting
from app.models.sequence.contact import SequenceContact, SequencePersonStage
from app.models.sequence.mail_history import (
    MailHistoryBounceSubType,
    MailHistoryBounceType,
    MailHistoryStatus,
    SequenceMailHistory,
)
from app.models.sequence.person_statistics import SequencePersonStatistics

status_list = [
    {
        "BounceType": MailHistoryBounceType.PERMANENT,
        "BounceSubType": MailHistoryBounceSubType.GENERAL,
        "BounceStatus": [
            "5.1.1",
            "5.1.2",
            "5.1.3",
            "5.1.4",
            "5.1.5",
            "5.1.6",
            "5.1.7",
            "5.1.8",
            "5.1.9",
        ],
    },
    {
        "BounceType": MailHistoryBounceType.PERMANENT,
        "BounceSubType": MailHistoryBounceSubType.NO_EMAIL,
        "BounceStatus": ["5.1.5"],
    },
    {
        "BounceType": MailHistoryBounceType.PERMANENT,
        "BounceSubType": MailHistoryBounceSubType.SUPPRESSED,
        "BounceStatus": ["5.7.1"],
    },
    {
        "BounceType": MailHistoryBounceType.PERMANENT,
        "BounceSubType": MailHistoryBounceSubType.ON_ACCOUNT_SUPPRESSION_LIST,
        "BounceStatus": ["5.7.2"],
    },
    {
        "BounceType": MailHistoryBounceType.TRANSIENT,
        "BounceSubType": MailHistoryBounceSubType.GENERAL,
        "BounceStatus": ["4.1.1", "4.1.2", "4.1.3", "4.1.4", "4.1.5", "4.4.2", "4.5.1"],
    },
    {
        "BounceType": MailHistoryBounceType.TRANSIENT,
        "BounceSubType": MailHistoryBounceSubType.MAILBOX_FULL,
        "BounceStatus": ["4.2.2"],
    },
    {
        "BounceType": MailHistoryBounceType.TRANSIENT,
        "BounceSubType": MailHistoryBounceSubType.MESSAGE_TOO_LARGE,
        "BounceStatus": ["4.3.1"],
    },
    {
        "BounceType": MailHistoryBounceType.TRANSIENT,
        "BounceSubType": MailHistoryBounceSubType.CONTENT_REJECTED,
        "BounceStatus": ["4.7.1"],
    },
    {
        "BounceType": MailHistoryBounceType.TRANSIENT,
        "BounceSubType": MailHistoryBounceSubType.ATTACHMENT_REJECTED,
        "BounceStatus": ["4.6.1"],
    },
]


def bounce_status_code_handler(status_code: str):
    for status in status_list:
        if status_code in status["BounceStatus"]:
            return {
                "BounceType": status["BounceType"],
                "BounceSubType": status["BounceSubType"],
            }
    return {
        "BounceType": MailHistoryBounceType.UNDETERMINED,
        "BounceSubType": MailHistoryBounceSubType.UNDETERMINED,
    }


def update_bounced_mail(
    db: Session,
    mail_history: SequenceMailHistory,
    status: str,
    diag_code: str,
    now: datetime,
):
    bounce_type = bounce_status_code_handler(status)
    mail_history.status = MailHistoryStatus.BOUNCED
    mail_history.bounce_type = bounce_type.get("BounceType")
    mail_history.bounce_sub_type = bounce_type.get("BounceSubType")
    mail_history.diag_code = diag_code
    mail_history.updated_at = now
    mail_history.bounced_at = now
    db.add(mail_history)
    # cập nhật person_stats last activity
    person_stats = db.exec(
        select(SequencePersonStatistics).where(
            SequencePersonStatistics.sequence_person_id
            == mail_history.sequence_contact_id,
            SequencePersonStatistics.deleted_at.is_(None),
        )
    ).first()
    if person_stats:
        person_stats.last_activity = now
    else:
        person_stats = SequencePersonStatistics(
            sequence_person_id=mail_history.sequence_contact_id, last_activity=now
        )
    db.add(person_stats)
    db.exec(
        update(SequenceContact)
        .where(SequenceContact.id == mail_history.sequence_contact_id)
        .values(
            stage=SequencePersonStage.BAD_DATA,
            status=StatusEnum.BOUNCED,
            updated_at=now,
        )
    )
    db.exec(
        update(SequenceCampaignContacts)
        .where(
            SequenceCampaignContacts.sequence_contact_id
            == mail_history.sequence_contact_id,
            SequenceCampaignContacts.sequence_campaign_id
            == mail_history.sequence_campaign_id,
        )
        .values(status=StatusEnum.BOUNCED, updated_at=now)
    )
    db.flush()
    db.refresh(mail_history)

    return mail_history


def update_replied_mail(
    db: Session, replied_mails: List[SequenceMailHistory], now: datetime
):
    for mail_history in replied_mails:
        mail_history.status = MailHistoryStatus.REPLIED
        mail_history.replied_at = now
        mail_history.updated_at = now
        # cập nhật person_stats last activity
        person_stats = db.exec(
            select(SequencePersonStatistics).where(
                SequencePersonStatistics.sequence_person_id
                == mail_history.sequence_contact_id,
                SequencePersonStatistics.deleted_at.is_(None),
            )
        ).first()
        if person_stats:
            person_stats.last_activity = now
        else:
            person_stats = SequencePersonStatistics(
                sequence_person_id=mail_history.sequence_contact_id, last_activity=now
            )
        db.add(person_stats)
    person_id_list = [
        mail_history.sequence_contact_id for mail_history in replied_mails
    ]
    db.add_all(replied_mails)
    result = db.exec(
        select(SequenceContact, SequenceCampaignSetting)
        .join(
            SequenceCampaignSetting,
            SequenceContact.sequence_campaign_id
            == SequenceCampaignSetting.sequence_campaign_id,
        )
        .where(SequenceContact.id.in_(person_id_list))
    ).all()
    continue_sequence_list = []
    person_list = []
    for person, campaign_setting in result:
        person.stage = SequencePersonStage.REPLIED
        person.status = StatusEnum.FINISH
        person.updated_at = now
        person_list.append(person)
        if campaign_setting.is_finished_when_replied is False:
            continue
        continue_sequence_list.append(
            (person.id, campaign_setting.sequence_campaign_id)
        )
    db.exec(
        update(SequenceCampaignContacts)
        .where(
            tuple_(
                SequenceCampaignContacts.sequence_contact_id,
                SequenceCampaignContacts.sequence_campaign_id,
            ).in_(continue_sequence_list)
        )
        .values(status=StatusEnum.FINISH, updated_at=now)
    )
    db.flush()
    return replied_mails
