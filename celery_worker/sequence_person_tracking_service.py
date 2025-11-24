from datetime import datetime, timedelta

from sqlmodel import Session, and_, func, select

from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.campaign_setting import SequenceCampaignSetting
from app.models.sequence.contact import SequenceContact, SequencePersonStage
from app.models.sequence.mail_history import MailHistoryStatus, SequenceMailHistory


def tracking_unresponsive_person(db: Session):
    print("Start tracking unresponsive sequence contact")
    query = (
        select(
            SequenceContact,
            SequenceCampaignSetting,
            func.max(SequenceMailHistory.sent_at),
        )
        .join(
            SequenceCampaignSetting,
            SequenceCampaignSetting.sequence_campaign_id
            == SequenceContact.sequence_campaign_id,
        )
        .join(
            SequenceMailHistory,
            SequenceMailHistory.sequence_contact_id == SequenceContact.id,
        )
        .join(
            SequenceCampaignContacts,
            and_(
                SequenceCampaignContacts.sequence_contact_id == SequenceContact.id,
                SequenceCampaignContacts.sequence_campaign_id
                == SequenceContact.sequence_campaign_id,
            ),
        )
        .where(
            SequenceContact.deleted_at.is_(None),
            SequenceContact.stage != SequencePersonStage.REPLIED.value,
            SequenceCampaignContacts.status == StatusEnum.FINISH.value,
            SequenceMailHistory.deleted_at.is_(None),
            SequenceMailHistory.status.in_(
                [
                    MailHistoryStatus.SENT,
                    MailHistoryStatus.OPENED,
                ]
            ),
        )
        .group_by(SequenceContact.id, SequenceCampaignSetting.id)
    )
    results = db.exec(query).all()
    now = datetime.now()
    unresponsive_person = []
    unresponsive_person_ids = []
    for person, campaign_setting, last_sent_at in results:
        if campaign_setting.days_until_unresponsive is None:
            continue
        if now - last_sent_at > timedelta(
            days=campaign_setting.days_until_unresponsive
        ):
            person.stage = SequencePersonStage.UNRESPONSIVE.value
            person.updated_at = now
            unresponsive_person.append(person)
            unresponsive_person_ids.append(person.id)
    db.add_all(unresponsive_person)
    db.commit()
    print("Finish tracking unresponsive sequence contact")
    return unresponsive_person_ids
