from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

import app.api.v1.services.events as events_service
import app.api.v1.services.events as event_service
from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.schemas.events import GetEventResponse

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/", response_model=GetEventResponse)
def listing_all_events(
    db: Session = Depends(get_session),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
):
    events, total, unlimited_total = events_service.listing_all_events(
        db, per_page, page
    )
    return GetEventResponse(data=events, total=total, unlimited_total=unlimited_total)


@router.get(
    "/listing-by-corporate_number/{corporate_number}",
    response_model=GetEventResponse,
)
def listing_event_by_corporate_number(
    corporate_number: str,
    db: Session = Depends(get_session),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
):
    events, total, unlimited_total = event_service.listing_event_by_corporate_number(
        corporate_number, db, per_page, page
    )
    return GetEventResponse(data=events, total=total, unlimited_total=unlimited_total)
