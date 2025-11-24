from typing import Optional

from fastapi import APIRouter, Depends

from app.api.base.deps import custom_generate_unique_id
from app.api.v1.dependencies import get_current_user, get_placeholder_sevice
from app.api.v1.schemas.placeholders import (
    ListingPlaceholderResponse,
    Placeholder,
    PlaceholderDetailResponse,
    UpsertPlaceholderRequest,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.placeholder import PlaceholderService

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/", response_model=ListingPlaceholderResponse)
def listing_placeholders(
    placeholder_sevice: PlaceholderService = Depends(get_placeholder_sevice),
    current_user: UserBase = Depends(get_current_user()),
    page: Optional[int] = None,
    per_page: Optional[int] = None,
    keyword: Optional[str] = None,
):
    placeholders = placeholder_sevice.listing_placeholders(
        current_user, page, per_page, keyword
    )
    total = placeholder_sevice.listing_placeholders_count(current_user, keyword)
    return ListingPlaceholderResponse(
        page=page, per_page=per_page, total=total, data=placeholders
    )


@router.get("/{placeholder_id}", response_model=PlaceholderDetailResponse)
def get_placeholder_detail(
    placeholder_id: int,
    placeholder_sevice: PlaceholderService = Depends(get_placeholder_sevice),
    current_user: UserBase = Depends(get_current_user()),
):
    name, placeholder = placeholder_sevice.get_placeholder_detail(
        placeholder_id, current_user
    )
    return PlaceholderDetailResponse(name=name, placeholder=placeholder)


@router.post("/", response_model=int)
def create_placeholder(
    placeholder_request: UpsertPlaceholderRequest,
    placeholder_sevice: PlaceholderService = Depends(get_placeholder_sevice),
    current_user: UserBase = Depends(get_current_user()),
):
    return placeholder_sevice.create_placeholder(placeholder_request, current_user)


@router.patch("/{placeholder_id}", response_model=Placeholder)
def update_placeholder(
    placeholder_id: int,
    placeholder_request: UpsertPlaceholderRequest,
    placeholder_sevice: PlaceholderService = Depends(get_placeholder_sevice),
    current_user: UserBase = Depends(get_current_user()),
):
    return placeholder_sevice.update_placeholder(
        placeholder_id, placeholder_request, current_user
    )
