from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.models import Person, PersonOptOut


def get_person_by_uuid(db: Session, person_uuid: str):
    person = db.exec(
        select(Person)
        .outerjoin(PersonOptOut, Person.uuid == PersonOptOut.person_uuid)
        .where(
            Person.uuid == person_uuid,
            PersonOptOut.person_uuid.is_(None),
        )
    ).first()

    if not person:
        raise NotFoundException(detail="person.personNotFound")

    return person
