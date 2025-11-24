from datetime import datetime

from sqlmodel import Session, update

from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum


def resume_campaign_person_service(db: Session):
    db.exec(
        update(SequenceCampaignContacts)
        .where(
            SequenceCampaignContacts.status == StatusEnum.PAUSE,
            SequenceCampaignContacts.time_resumed <= datetime.now(),
            SequenceCampaignContacts.deleted_at.is_(None),
        )
        .values(status=StatusEnum.ACTIVE)
    )
    db.commit()
