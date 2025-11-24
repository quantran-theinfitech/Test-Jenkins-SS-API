from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.v1.schemas.sequence.persons import (
    SequenceCampaignWithPersonStatus,
    SequencePersonDetail,
)
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_contacts import SequenceCampaignContacts
from app.models.sequence.contact import SequenceContact
from app.models.sequence.task import SequenceTask


def get_detail_sequence_person_service(
    sequence_campaign_id: int,
    person_id: int,
    db: Session,
):
    campaigns = []
    tasks = []
    condition = [
        SequenceContact.id == person_id,
        SequenceContact.sequence_campaign_id == sequence_campaign_id,
        SequenceContact.deleted_at.is_(None),
    ]
    query = select(SequenceContact).where(*condition)
    person = db.exec(query).first()
    if not person:
        raise HTTPException(status_code=404, detail="sequence.personNotFound")

    condition = [
        SequenceCampaign.id == sequence_campaign_id,
        SequenceCampaign.deleted_at.is_(None),
    ]
    query = select(SequenceCampaign).where(*condition)
    campaign = db.exec(query).first()
    if campaign:
        condition = [
            SequenceCampaignContacts.sequence_campaign_id == sequence_campaign_id,
            SequenceCampaignContacts.sequence_contact_id == person_id,
            SequenceCampaignContacts.deleted_at.is_(None),
        ]
        query = select(SequenceCampaignContacts.status).where(*condition)
        status = db.exec(query).first()
        campaigns.append(
            SequenceCampaignWithPersonStatus(**campaign.dict(), status=status)
        )
    condition = [
        SequenceTask.sequence_person_id == person_id,
        SequenceTask.sequence_campaign_id == sequence_campaign_id,
        SequenceTask.deleted_at.is_(None),
    ]
    query = select(SequenceTask).where(*condition)
    tasks = db.exec(query).all()

    return SequencePersonDetail(**person.dict(), campaigns=campaigns, tasks=tasks)
