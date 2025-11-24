from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

import app.api.v1.services.tracking_urls as tracking_urls_service
from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.tracking_urls import (
    CreateTrackingUrlRequest,
    CreateTrackingUrlResponse,
    GetTrackingUrlDetail,
    ListingTrackingUrlResponse,
)
from app.api.v1.schemas.users import UserBase

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/", response_model=ListingTrackingUrlResponse)
def listing_tracking_urls(
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    keyword: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    tracking_urls = tracking_urls_service.listing_tracking_urls(
        db, current_user, page, per_page, keyword
    )
    total = tracking_urls_service.listing_tracking_urls_count(db, current_user, keyword)
    return ListingTrackingUrlResponse(
        page=page, per_page=per_page, total=total, data=tracking_urls
    )


@router.get("/{tracking_url_id}", response_model=GetTrackingUrlDetail)
def get_tracking_url_detail(
    tracking_url_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    tracking_url_detail = tracking_urls_service.get_tracking_url_detail(
        db, current_user, tracking_url_id
    )
    clickable_count = tracking_urls_service.get_clickable_tracking_url_count(
        db, tracking_url_id
    )

    return GetTrackingUrlDetail(**tracking_url_detail, clickable_count=clickable_count)


@router.post("/", response_model=CreateTrackingUrlResponse)
def create_tracking_url(
    request: CreateTrackingUrlRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):

    tracking_url = tracking_urls_service.create_tracking_url(db, current_user, request)
    return tracking_url
