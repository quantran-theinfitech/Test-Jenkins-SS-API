from typing import List, Optional

from sqlalchemy import distinct, func
from sqlmodel import Session, col, desc, select

from app.api.v1.schemas.person_exclude_collections import (
    ListingPersonExcludeCollectionItem,
)
from app.models.person_exclude_collection import PersonExcludeCollection
from app.models.person_exclude_collection_item import PersonExcludeCollectionItem
from app.models.user import User


def listing_all_person_exclude_collections(
    db: Session,
    current_user: User,
    keyword: Optional[str] = None,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
) -> List[ListingPersonExcludeCollectionItem]:
    query = (
        select(
            PersonExcludeCollection.id,
            PersonExcludeCollection.team_id,
            PersonExcludeCollection.name,
            PersonExcludeCollection.type_code,
            PersonExcludeCollection.identification_rate,
            PersonExcludeCollection.csv_path,
            PersonExcludeCollection.created_at,
            PersonExcludeCollection.created_by,
            func.count(distinct(PersonExcludeCollectionItem.person_uuid)).label(
                "persons_count"
            ),
        )
        .join(
            PersonExcludeCollectionItem,
            PersonExcludeCollectionItem.collection_id == PersonExcludeCollection.id,
            isouter=True,
        )
        .where(PersonExcludeCollection.team_id == current_user.team_id)
    )
    query = query.order_by(desc(PersonExcludeCollection.id)).group_by(
        PersonExcludeCollection.id
    )

    if page is not None and per_page is not None:
        query = query.offset((page - 1) * per_page)
        query = query.limit(per_page)

    if keyword is not None:
        query = query.where(col(PersonExcludeCollection.name).ilike(f"%{keyword}%"))

    person_exclude_collections = db.execute(query).all()
    return person_exclude_collections


def count_listing_all_person_exclude_collections(
    db: Session, current_user: User, keyword: Optional[str] = None
):
    total_query = select(PersonExcludeCollection).where(
        PersonExcludeCollection.team_id == current_user.team_id
    )
    if keyword is not None:
        total_query = total_query.where(
            col(PersonExcludeCollection.name).ilike(f"%{keyword}%")
        )
    total = (
        db.execute(
            total_query.with_only_columns(
                func.count(distinct(PersonExcludeCollection.id))
            )
        ).scalar()
        or 0
    )

    return total
