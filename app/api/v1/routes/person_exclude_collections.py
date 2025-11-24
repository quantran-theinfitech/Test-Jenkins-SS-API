from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

import app.api.v1.services.person_exclude_collections as exclude_collection_service
from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.person_exclude_collections import (
    CreatePersonExcludeCollectionByIdsRequest,
    ExcludeCollectionPersonsResponse,
    ListingPersonExcludeCollectionResponse,
    PersonExcludeCollectionDetailResponse,
)
from app.api.v1.schemas.users import UserBase
from app.models.user import User

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.post("", response_model=int)
def create_person_exclude_collections(
    request: CreatePersonExcludeCollectionByIdsRequest,
    user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    excludeCollection = exclude_collection_service.create_person_exclude_collections(
        request, user, db
    )
    return excludeCollection


@router.get(
    "/{exclude_collection_id}", response_model=PersonExcludeCollectionDetailResponse
)
def get_person_exclude_collection_detail(
    exclude_collection_id: int,
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return exclude_collection_service.get_person_exclude_collection_detail(
        db, exclude_collection_id, current_user.team_id
    )


@router.get("/{exclude_id}/persons", response_model=ExcludeCollectionPersonsResponse)
def listing_person_exclude_collection_persons(
    exclude_id: int,
    current_user: User = Depends(get_current_user()),
    keyword: Optional[str] = None,
    per_page: Optional[int] = Query(default=10, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    db: Session = Depends(get_session),
):
    persons = exclude_collection_service.listing_person_exclude_collection_persons(
        exclude_id, current_user.team_id, keyword, db, page, per_page
    )
    total = exclude_collection_service.get_person_exclude_collection_persons_count(
        db, exclude_id, current_user.team_id, keyword
    )
    return ExcludeCollectionPersonsResponse(
        page=page, per_page=per_page, total=total, data=persons
    )


@router.get("", response_model=ListingPersonExcludeCollectionResponse)
def listing_all_person_exclude_collections(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user()),
    keyword: Optional[str] = Query(default=None),
    page: Optional[int] = None,
    per_page: Optional[int] = None,
):
    collections = exclude_collection_service.listing_all_person_exclude_collections(
        db, current_user, keyword, page, per_page
    )

    total = exclude_collection_service.count_listing_all_person_exclude_collections(
        db,
        current_user,
        keyword,
    )
    return ListingPersonExcludeCollectionResponse(
        per_page=per_page,
        current_page=page,
        total=total,
        data=collections,
    )
