from random import randint, choice
from app.api.v1.schemas.sequence.schedules import (
    SendingWindow,
    ScheduleBase,
    ListingScheduleResponse,
)


def generate_mock_sending_window() -> SendingWindow:
    start_time = f"2025-01-23T{randint(8, 12)}:00:00"
    end_time = f"2025-01-23T{randint(13, 17)}:00:00"
    return SendingWindow(start_time=start_time, end_time=end_time)


def generate_mock_schedule(id: int) -> ScheduleBase:
    time_zones = [
        "UTC",
        "Asia/Tokyo",
        "America/New_York",
        "Europe/London",
        "Asia/Singapore",
    ]
    return ScheduleBase(
        id=id,
        name=f"Schedule {id}",
        time_zone=choice(time_zones),
        sending_window=[generate_mock_sending_window() for _ in range(randint(1, 3))],
    )


def generate_mock_listing_schedule(page: int, per_page: int) -> ListingScheduleResponse:
    total = 50
    data = [
        generate_mock_schedule(id)
        for id in range((page - 1) * per_page + 1, page * per_page + 1)
    ]
    return ListingScheduleResponse(page=page, per_page=per_page, total=total, data=data)
