from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.base.deps import custom_generate_unique_id
from app.api.v1.dependencies import get_current_user, get_group_service
from app.api.v1.schemas.groups import (
    Collection,
    CreateGroupRequest,
    GetGroupResponse,
    ListingGroupResponse,
    ListingPersonCollectionsResponse,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.group_service import GroupService
from app.models.company_collection import StatusCode

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/", response_model=ListingGroupResponse)
def listing_groups(
    page: Optional[int] = None,
    per_page: Optional[int] = None,
    keyword: Optional[str] = Query(default=None),
    group_service: GroupService = Depends(get_group_service),
    current_user: UserBase = Depends(get_current_user()),
):
    list_group, total = group_service.listing_groups(
        current_user, page, per_page, keyword
    )
    return ListingGroupResponse(
        current_page=page, per_page=per_page, total=total, data=list_group
    )


@router.post("/", response_model=int)
def create_group(
    request_body: CreateGroupRequest,
    current_user: UserBase = Depends(get_current_user()),
    group_service: GroupService = Depends(get_group_service),
):
    return group_service.create_group(request_body, current_user)


@router.get("/{id}", response_model=GetGroupResponse)
def get_group_detail(
    id: int,
    status_code: Optional[StatusCode] = None,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
    keyword: Optional[str] = Query(default=None),
    group_service: GroupService = Depends(get_group_service),
    user: UserBase = Depends(get_current_user()),
):
    group = group_service.get_group_detail(id, user)
    total = group_service.count_group_collections(user, id, status_code, keyword)
    collections = group_service.listing_group_collections(
        user, id, status_code, page, per_page, keyword
    )
    collectionItems = []
    for row in collections:
        collectionItems.append(
            Collection(
                id=row.id,
                name=row.name,
                description=row.description,
                status_code=row.status_code,
                companies_count=row.companies_count,
                assignees=row.assignees or [],
                tags=row.tags or [],
                created_at=row.created_at,
            )
        )

    return GetGroupResponse(
        per_page=per_page,
        current_page=page,
        total=total,
        id=group.id,
        name=group.name,
        team_id=group.team_id,
        description=group.description,
        created_at=group.created_at,
        collections=collectionItems,
    )


@router.get(
    "/{id}/listing-person-collections", response_model=ListingPersonCollectionsResponse
)
def listing_group_person_collections(
    id: int,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
    current_user: UserBase = Depends(get_current_user()),
    group_service: GroupService = Depends(get_group_service),
):
    listing_person_cols, total = group_service.listing_person_collections(
        id, current_user, page, per_page
    )
    data = [r for r, in listing_person_cols]

    return ListingPersonCollectionsResponse(
        per_page=per_page,
        current_page=page,
        total=total,
        data=data,
    )
