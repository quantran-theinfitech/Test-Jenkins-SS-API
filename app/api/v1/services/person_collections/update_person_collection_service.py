import datetime

from sqlmodel import Session, select

from app.api.base.exceptions import BadRequestException, NotFoundException
from app.api.v1.schemas.person_collections import UpdatePersonCollectionRequest
from app.models import PersonCollection
from app.models.user import User


def update_person_collection(
    db: Session,
    collection_id: int,
    current_user: User,
    request: UpdatePersonCollectionRequest,
):
    person_collection = db.exec(
        select(PersonCollection)
        .where(PersonCollection.team_id == current_user.team_id)
        .where(PersonCollection.id == collection_id)
    ).first()
    if not person_collection:
        raise NotFoundException(detail="person.notFound")
    if request.name:
        existing_collection = db.exec(
            select(PersonCollection)
            .where(PersonCollection.team_id == current_user.team_id)
            .where(PersonCollection.name == request.name)
            .where(PersonCollection.id != collection_id)
        ).first()
        if existing_collection:
            raise BadRequestException(detail="common.duplicateName")
    for attr, value in request.dict(exclude_unset=True).items():
        setattr(person_collection, attr, value)
    person_collection.updated_by = current_user.id
    person_collection.updated_at = datetime.datetime.now()
    db.add(person_collection)
    db.commit()
    db.refresh(person_collection)
    return person_collection
