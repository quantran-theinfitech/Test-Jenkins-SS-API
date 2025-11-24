from datetime import datetime, timedelta
from typing import Optional

import pytz
from sqlmodel import Session, select

from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.schedule import SequenceCampaignSchedule
from app.models.sequence.schedule_sending_windows import (
    SequenceCampaignScheduleSendingWindows,
)


def get_next_weekday_date(start_date, target_weekday_num):
    current_weekday = start_date.weekday()
    days_until_target = (target_weekday_num - current_weekday + 7) % 7

    # If the target weekday is today, and we want the *next* occurrence, add 7 days
    if days_until_target == 0 and start_date.weekday() == target_weekday_num:
        days_until_target = 7

    next_date = start_date + timedelta(days=days_until_target)
    return next_date


def validate_campaign_on_sending_window(
    db: Session, campaign_id, due_date: Optional[datetime] = None
):
    campaign = db.get(SequenceCampaign, campaign_id)

    # schedule_id = campaign.schedule_id
    schedule = db.get(SequenceCampaignSchedule, campaign.schedule_id)
    if not schedule:
        schedule = db.exec(
            select(SequenceCampaignSchedule).where(
                SequenceCampaignSchedule.team_id == campaign.team_id,
                SequenceCampaignSchedule.is_default.is_(True),
            )
        ).first()

    if not schedule:
        return True, None

    timezone = "UTC"

    if schedule.time_zone:
        timezone = schedule.time_zone

    now = datetime.now(pytz.timezone(timezone))
    if due_date:
        now = due_date.astimezone(pytz.timezone(timezone))
    sending_windows = db.exec(
        select(SequenceCampaignScheduleSendingWindows).where(
            SequenceCampaignScheduleSendingWindows.schedule_id == schedule.id,
            SequenceCampaignScheduleSendingWindows.deleted_at.is_(None),
        )
    ).all()

    sending_window_mapping = {}

    for window in sending_windows:
        if sending_window_mapping.get(window.week_day) is None:
            sending_window_mapping[window.week_day] = []
        sending_window_mapping[window.week_day].append(
            {
                "start_time": window.start_time,
                "end_time": window.end_time,
            }
        )
    schedule_time = None
    for window in sending_window_mapping.get(now.weekday(), []):
        if window["start_time"] <= now.hour <= window["end_time"]:
            return True, None
        if window["start_time"] > now.hour:
            if schedule_time is None or window["start_time"] < schedule_time:
                schedule_time = now.replace(
                    hour=window["start_time"], minute=0, second=0, microsecond=0
                )
    if schedule_time:
        return False, schedule_time

    schedule_weekday_date = None
    if now.weekday() >= max(schedule.days_per_week):
        schedule_weekday_date = get_next_weekday_date(
            now.date(), min(schedule.days_per_week)
        )
    else:
        for i in range(1, 7):
            if sending_window_mapping.get(now.weekday() + i, False):
                schedule_weekday_date = get_next_weekday_date(
                    now.date(), now.weekday() + i
                )
                break

    if schedule_weekday_date:
        schedule_hour = min(
            [
                swm["start_time"]
                for swm in sending_window_mapping.get(
                    schedule_weekday_date.weekday(), []
                )
            ]
        )
        schedule_datetime = now.replace(
            year=schedule_weekday_date.year,
            month=schedule_weekday_date.month,
            day=schedule_weekday_date.day,
            hour=schedule_hour,
            minute=0,
            second=0,
        )

        return False, schedule_datetime

    return False, None
