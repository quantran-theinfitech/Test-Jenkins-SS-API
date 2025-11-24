from datetime import datetime, timedelta, timezone
from typing import Optional

import pytz

from app.api.v1.schemas.sequence.mail_histories import ScheduleType


def handle_schedule_immediately():
    return datetime.now(timezone.utc)


def handle_schedule_one_hour():
    return datetime.now(timezone.utc) + timedelta(hours=1)


def handle_schedule_two_hour():
    return datetime.now(timezone.utc) + timedelta(hours=2)


def handle_schedule_a_day():
    return datetime.now(timezone.utc) + timedelta(days=1)


def handle_schedule_a_week():
    return datetime.now(timezone.utc) + timedelta(days=7)


def handle_schedule_a_month():
    return datetime.now(timezone.utc) + timedelta(days=30)


def get_next_business_day():
    for i in range(1, 7):
        next_day = datetime.now(pytz.timezone("Asia/Tokyo")) + timedelta(days=i)
        if next_day.weekday() < 5:
            return next_day

    raise Exception("Cannot find next business day")


def handle_schedule_next_business_day_morning():
    next_day = get_next_business_day()
    return datetime(
        next_day.year,
        next_day.month,
        next_day.day,
        8,
        0,
        0,
        0,
    )


def handle_schedule_next_business_day_afternoon():
    next_day = get_next_business_day()
    return datetime(
        next_day.year,
        next_day.month,
        next_day.day,
        13,
        0,
        0,
        0,
    )


SCHEDULE_TIME_HANDLER = {
    ScheduleType.IMMEDIATELY: handle_schedule_immediately,
    ScheduleType.ONE_HOUR: handle_schedule_one_hour,
    ScheduleType.TWO_HOUR: handle_schedule_two_hour,
    ScheduleType.A_DAY: handle_schedule_a_day,
    ScheduleType.A_WEEK: handle_schedule_a_week,
    ScheduleType.A_MONTH: handle_schedule_a_month,
    ScheduleType.NEXT_BUSINESS_DAY_MORNING: handle_schedule_next_business_day_morning,
    ScheduleType.NEXT_BUSINESS_DAY_AFTERNOON: (
        handle_schedule_next_business_day_afternoon
    ),
}


def handle_schedule_time(
    schedule_type: ScheduleType, custom_datetime: Optional[datetime]
):
    if schedule_type == ScheduleType.CUSTOM and custom_datetime:
        return custom_datetime

    return SCHEDULE_TIME_HANDLER[schedule_type]()
