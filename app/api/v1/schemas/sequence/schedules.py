from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel


class SequenceType(Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class PriorityEnum(str, Enum):
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class SendingWindow(BaseModel):
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    week_day: Optional[Literal[0, 1, 2, 3, 4, 5, 6]] = None


class Timezone(str, Enum):
    PACIFIC_TIME = "America/Los_Angeles"
    MOUNTAIN_TIME = "America/Denver"
    CENTRAL_TIME = "America/Chicago"
    EASTERN_TIME = "America/New_York"
    UTC = "UTC"
    LONDON = "Europe/London"
    PARIS = "Europe/Paris"
    ATHENS = "Europe/Athens"
    AUSTRALIA_WESTERN_STANDARD_TIME = "Australia/Perth"
    AUSTRALIA_CENTRAL_STANDARD_TIME = "Australia/Adelaide"
    AUSTRALIA_EASTERN_STANDARD_TIME = "Australia/Sydney"
    MIDDLE_EAST_TIME = "Asia/Dubai"
    NEAR_EAST_TIME = "Asia/Beirut"
    PAKISTAN_LAHORE_TIME = "Asia/Karachi"
    INDIA_STANDARD_TIME = "Asia/Kolkata"
    BANGLADESH_STANDARD_TIME = "Asia/Dhaka"
    VIETNAM_STANDARD_TIME = "Asia/Ho_Chi_Minh"
    JAPAN_STANDARD_TIME = "Asia/Tokyo"
    SOLOMON_STANDARD_TIME = "Pacific/Guadalcanal"
    NEW_ZEALAND_STANDARD_TIME = "Pacific/Auckland"
    MIDWAY_ISLANDS_TIME = "Pacific/Midway"
    HAWAII_STANDARD_TIME = "Pacific/Honolulu"
    ALASKA_STANDARD_TIME = "America/Anchorage"
    PUERTO_RICO_AND_US_VIRGIN_ISLANDS_TIME = "America/Puerto_Rico"
    CANADA_NEWFOUNDLAND_TIME = "America/St_Johns"
    BRAZIL_EASTERN_TIME = "America/Sao_Paulo"


class CreateScheduleRequest(BaseModel):
    name: str
    time_zone: Optional[Timezone] = Timezone.JAPAN_STANDARD_TIME
    use_local_time_zone: Optional[bool] = None
    is_skip_holiday: Optional[bool] = None
    sending_windows: Optional[List[SendingWindow]] = None


class DefaultScheduleRequest(BaseModel):
    name: str = "通常業務時間"
    time_zone: Timezone = Timezone.JAPAN_STANDARD_TIME
    use_local_time_zone: bool = True
    is_skip_holiday: bool = True
    sending_windows: List[SendingWindow] = [
        SendingWindow(
            start_time=8,
            end_time=17,
            week_day=week_day,
        )
        for week_day in range(5)
    ]


class UpdateScheduleRequest(BaseModel):
    name: Optional[str] = None
    time_zone: Optional[Timezone] = None
    use_local_time_zone: Optional[bool] = None
    is_default: Optional[bool] = None
    is_skip_holiday: Optional[bool] = None
    sending_windows: Optional[List[SendingWindow]] = None


class DeleteScheduleRequest(BaseModel):
    new_default_schedule_id: int


class ScheduleBase(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    time_zone: Optional[str] = None
    is_skip_holiday: Optional[bool] = None
    use_local_time_zone: Optional[bool] = None
    sending_windows: Optional[List[SendingWindow]] = None
    days_per_week: Optional[List[int]] = None
    is_default: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ListingScheduleResponse(BaseModel):
    page: int
    per_page: int
    total: int
    data: List[ScheduleBase]
