from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.sequence.schedules import (
    CreateScheduleRequest,
    DeleteScheduleRequest,
    ListingScheduleResponse,
    ScheduleBase,
    UpdateScheduleRequest,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.schedules import (
    count_listing_schedules_service,
    create_schedule_service,
    delete_schedule_service,
    get_detail_schedule_service,
    listing_schedules_service,
    update_schedule_service,
)

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.post("/schedules", response_model=ScheduleBase)
def create_schedule(
    request_body: CreateScheduleRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return create_schedule_service(db, current_user, request_body)


@router.put("/schedules/{schedule_id}", response_model=ScheduleBase)
def update_schedule(
    schedule_id: int,
    request: UpdateScheduleRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return update_schedule_service(db, current_user, schedule_id, request)


@router.delete("/schedules/{schedule_id}", status_code=204)
def delete_schedule(
    schedule_id: int,
    request: DeleteScheduleRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return delete_schedule_service(db, current_user, schedule_id, request)


@router.get("/schedules", response_model=ListingScheduleResponse)
def listing_schedules(
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    data = listing_schedules_service(db, current_user, per_page, page)
    total = count_listing_schedules_service(db, current_user)
    return ListingScheduleResponse(
        page=page,
        per_page=per_page,
        total=total,
        data=data,
    )


@router.get("/schedules/{schedule_id}", response_model=ScheduleBase)
def get_detail_schedule(
    schedule_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return get_detail_schedule_service(schedule_id, db, current_user)
