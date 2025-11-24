from sqlmodel import Session

from app.api.v1.schemas.person_exclude_collections import (
    CreatePersonExcludeCollectionByIdsRequest,
)
from app.api.v1.schemas.users import UserBase
from app.models.person_exclude_collection import PersonExcludeCollection
from app.models.person_exclude_collection_item import PersonExcludeCollectionItem


def create_person_exclude_collections(
    request: CreatePersonExcludeCollectionByIdsRequest,
    user: UserBase,
    db: Session,
):
    try:
        exclude_collection = PersonExcludeCollection(
            name=request.name, description=request.description, team_id=user.team_id
        )
        db.add(exclude_collection)
        db.flush()

        exclude_collection_item = [
            PersonExcludeCollectionItem(
                person_uuid=pid, collection_id=exclude_collection.id
            )
            for pid in request.item_ids
        ]
        db.add_all(exclude_collection_item)
        db.commit()
        return exclude_collection.id
    except Exception as e:
        db.rollback()
        raise e
