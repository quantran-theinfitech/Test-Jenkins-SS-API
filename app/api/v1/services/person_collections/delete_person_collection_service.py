import datetime

from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.models import PersonCollection
from app.models.user import User


def delete_person_collection(db: Session, collection_id: int, current_user: User):
    person_collection = db.exec(
        select(PersonCollection)
        .where(PersonCollection.team_id == current_user.team_id)
        .where(PersonCollection.id == collection_id)
    ).first()
    if not person_collection:
        raise NotFoundException(detail="person.notFound")
    person_collection.deleted_by = current_user.id
    person_collection.deleted_at = datetime.datetime.now()
    db.add(person_collection)
    db.commit()
    db.refresh(person_collection)
    return person_collection.id
