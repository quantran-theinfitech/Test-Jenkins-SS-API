from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies.authentication import get_current_user
from app.api.v1.schemas.form_schedule import (
    CreateFormScheduleRequest,
    DeleteFormScheduleRequest,
    FormScheduleItem,
    ListingFormScheduleResponse,
    UpdateFormScheduleRequest,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services import form_schedule as form_schedule_service

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/schedules", response_model=ListingFormScheduleResponse)
def listing_form_schedules(
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    data = form_schedule_service.listing_form_schedules(
        db, current_user, per_page, page
    )
    total = form_schedule_service.count_listing_form_schedules(db, current_user)
    return ListingFormScheduleResponse(
        page=page,
        per_page=per_page,
        total=total,
        data=data,
    )


@router.post("/schedules", response_model=FormScheduleItem)
def create_form_schedule(
    request_body: CreateFormScheduleRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return form_schedule_service.create_form_schedule(db, current_user, request_body)


@router.get("/schedules/{form_schedule_id}", response_model=FormScheduleItem)
def get_form_schedule(
    form_schedule_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return form_schedule_service.get_form_schedule_detail(
        db, current_user, form_schedule_id
    )


@router.put("/schedules/{form_schedule_id}", response_model=FormScheduleItem)
def update_form_schedule(
    form_schedule_id: int,
    request: UpdateFormScheduleRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return form_schedule_service.update_form_schedule(
        db, current_user, form_schedule_id, request
    )


@router.delete("/schedules/{form_schedule_id}", status_code=204)
def delete_form_schedule(
    form_schedule_id: int,
    request: DeleteFormScheduleRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return form_schedule_service.delete_form_schedule(
        db, current_user, form_schedule_id, request
    )
