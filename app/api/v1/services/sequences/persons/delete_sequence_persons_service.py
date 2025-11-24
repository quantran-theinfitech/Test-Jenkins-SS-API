from datetime import datetime
from typing import List

from sqlmodel import Session, delete, select, update

from app.api.base.exceptions import NotFoundException
from app.models.sequence.campaign_contacts import SequenceCampaignContacts
from app.models.sequence.contact import SequenceContact
from app.models.sequence.mail_history import MailHistoryStatus, SequenceMailHistory
from app.models.sequence.task import SequenceTask


def delete_sequence_persons_service(db: Session, sequence_person_ids: List[int]):
    sequence_persons = db.exec(
        select(SequenceContact).where(SequenceContact.id.in_(sequence_person_ids))
    ).all()

    if not sequence_persons:
        raise NotFoundException(detail="sequence_person.notFound")

    for sequence_person in sequence_persons:
        sequence_person.deleted_at = datetime.now()
        db.add(sequence_person)
        db.execute(
            update(SequenceCampaignContacts)
            .where(SequenceCampaignContacts.sequence_contact_id == sequence_person.id)
            .values(deleted_at=datetime.now())
        )
        db.execute(
            update(SequenceMailHistory)
            .where(
                SequenceMailHistory.sequence_contact_id == sequence_person.id,
                SequenceMailHistory.status == MailHistoryStatus.SCHEDULED,
            )
            .values(deleted_at=datetime.now())
        )
        db.execute(
            delete(SequenceTask).where(
                SequenceTask.sequence_person_id == sequence_person.id
            )
        )
    db.commit()

    return [sequence_person.id for sequence_person in sequence_persons]
