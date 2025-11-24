from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.api.v1.schemas.sequence.schedules import SendingWindow, Timezone


class FormScheduleItem(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    time_zone: Optional[str] = None
    is_skip_holiday: Optional[bool] = None
    sending_windows: Optional[List[SendingWindow]] = None
    days_per_week: Optional[List[int]] = None
    is_default: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ListingFormScheduleResponse(BaseModel):
    page: Optional[int]
    per_page: Optional[int]
    total: int
    data: List[FormScheduleItem]


class DefaultFormScheduleRequest(BaseModel):
    name: str = "通常業務時間"
    time_zone: Timezone = Timezone.JAPAN_STANDARD_TIME
    is_skip_holiday: bool = True
    sending_windows: List[SendingWindow] = [
        SendingWindow(
            start_time=8,
            end_time=17,
            week_day=week_day,
        )
        for week_day in range(5)
    ]


class CreateFormScheduleRequest(BaseModel):
    name: str
    time_zone: Optional[Timezone] = Timezone.JAPAN_STANDARD_TIME
    is_skip_holiday: Optional[bool] = None
    sending_windows: Optional[List[SendingWindow]] = None


class UpdateFormScheduleRequest(BaseModel):
    name: Optional[str] = None
    time_zone: Optional[Timezone] = None
    is_skip_holiday: Optional[bool] = None
    sending_windows: Optional[List[SendingWindow]] = None
    is_default: Optional[bool] = None


class DeleteFormScheduleRequest(BaseModel):
    new_default_schedule_id: Optional[int] = None
