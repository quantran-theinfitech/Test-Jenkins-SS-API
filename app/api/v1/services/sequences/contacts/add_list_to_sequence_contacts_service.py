from datetime import datetime
from typing import Optional

from sqlmodel import Session, or_, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.users import UserBase
from app.models.person import Person
from app.models.person_collection import PersonCollection
from app.models.person_collection_item import PersonCollectionItem
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.contact import (
    ContactType,
    SequenceContact,
    SequencePersonStage,
)

from .create_sequence_contacts_service import FIELD_MAP


def add_list_to_sequence_contacts_service(
    sequence_campaign_id: int,
    list_id: int,
    db: Session,
    current_user: UserBase,
    is_include_incompleted_contacts: Optional[bool]
):
    exist_person_collection = db.exec(
        select(PersonCollection).where(
            PersonCollection.id == list_id,
            PersonCollection.team_id == current_user.team_id,
            PersonCollection.deleted_at.is_(None),
        )
    ).first()
    if not exist_person_collection:
        raise NotFoundException(detail="person.ListNotFound")
    exist_seq = db.exec(
        select(SequenceCampaign).where(
            SequenceCampaign.id == sequence_campaign_id,
            SequenceCampaign.deleted_at.is_(None),
            SequenceCampaign.team_id == current_user.team_id,
        )
    ).first()
    if not exist_seq:
        raise NotFoundException(detail="sequence.SequenceNotFound")
    exist_subq = db.exec(
        select(SequenceContact.uuid).where(
            SequenceContact.sequence_campaign_id == sequence_campaign_id,
            SequenceContact.deleted_at.is_(None)
        )
    ).all()

    list_uuids_to_add = db.exec(
        select(PersonCollectionItem.person_uuid).where(
            PersonCollectionItem.collection_id == list_id,
            PersonCollectionItem.person_uuid.not_in(exist_subq),
            PersonCollectionItem.deleted_at.is_(None),
        )
    ).all()
    if not list_uuids_to_add:
        return None

    if is_include_incompleted_contacts is True:
        person_contacts = db.exec(
            select(Person).where(
                Person.uuid.in_(list_uuids_to_add)
            )
        ).all()
    else:
        person_contacts = db.exec(
            select(Person).where(
                Person.uuid.in_(list_uuids_to_add),
                or_(
                    Person.email.is_not(None),
                    Person.linkedin_url.is_not(None)
                )
            )
        ).all()
    contact_map = {person.uuid: person for person in person_contacts}

    CHUNK_SIZE = 500
    try:
        for batch in range(0, len(list_uuids_to_add), CHUNK_SIZE):
            new_contacts = []
            new_campaign_contacts = []

            for _i in range(batch, batch + CHUNK_SIZE):
                if _i >= len(list_uuids_to_add):
                    break
                contact = contact_map.get(list_uuids_to_add[_i])
                if not contact:
                    continue
                values = {}
                for model_field, contact_key in FIELD_MAP.items():
                    val = getattr(contact, contact_key)
                    values[model_field] = val

                new_contact = SequenceContact(
                    uuid=list_uuids_to_add[_i],
                    sequence_campaign_id=sequence_campaign_id,
                    target_type=ContactType.PERSON,
                    current_step=1,
                    stage=SequencePersonStage.COLD,
                    created_at=datetime.now(),
                    created_by=current_user.id,
                    status=StatusEnum.ACTIVE
                    if exist_seq.is_active
                    else StatusEnum.PAUSE,
                    **values,
                )
                new_contacts.append(new_contact)
            db.add_all(new_contacts)
            db.commit()
            for new_contact in new_contacts:
                new_campaign_contacts.append(
                    SequenceCampaignContacts(
                        sequence_campaign_id=sequence_campaign_id,
                        sequence_contact_id=new_contact.id,
                        created_at=datetime.now(),
                        created_by=current_user.id,
                        status=StatusEnum.ACTIVE
                        if exist_seq.is_active
                        else StatusEnum.PAUSE,
                        time_resumed=datetime.now() 
                        if exist_seq.is_active 
                        else None
                    )
                )
            db.add_all(new_campaign_contacts)
            db.commit()
    except Exception as e:
        print(e)
        db.rollback()
        raise e

    return sequence_campaign_id
