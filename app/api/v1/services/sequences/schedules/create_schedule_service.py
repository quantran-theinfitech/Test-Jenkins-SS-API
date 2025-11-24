from datetime import datetime
from typing import List

from fastapi import HTTPException
from sqlmodel import Session

from app.api.v1.schemas.sequence.schedules import (
    CreateScheduleRequest,
    ScheduleBase,
    SendingWindow,
    Timezone,
)
from app.api.v1.schemas.users import UserBase
from app.models.sequence.schedule import SequenceCampaignSchedule
from app.models.sequence.schedule_sending_windows import (
    SequenceCampaignScheduleSendingWindows,
)

from .get_detail_schedules_services import get_default_schedule


def check_valid_sending_windows(sending_windows: List[SendingWindow]) -> bool:
    if sending_windows == []:
        raise HTTPException(status_code=400, detail="sequence.emptySendingWindows")
    if sending_windows:
        for window in sending_windows:
            if window.start_time > window.end_time:
                return False
    return True


def create_schedule_service(
    db: Session, current_user: UserBase, request: CreateScheduleRequest
):
    if not check_valid_sending_windows(request.sending_windows):
        raise HTTPException(status_code=400, detail="sequence.TimeIsInvalid")
    if not request.name:
        raise HTTPException(status_code=400, detail="sequence.nameIsRequired")

    name_exists = (
        db.query(SequenceCampaignSchedule)
        .filter(
            SequenceCampaignSchedule.name == request.name,
            SequenceCampaignSchedule.deleted_at.is_(None),
            SequenceCampaignSchedule.team_id == current_user.team_id,
        )
        .first()
    )

    if name_exists:
        raise HTTPException(status_code=400, detail="sequence.duplicateName")
    if len(request.name) > 256:
        raise HTTPException(status_code=400, detail="sequence.nameIsTooLong")
    time_zone = request.time_zone if request.time_zone else Timezone.JAPAN_STANDARD_TIME

    use_local_time_zone = (
        request.use_local_time_zone
        if request.use_local_time_zone is not None
        else False
    )
    is_skip_holiday = (
        request.is_skip_holiday if request.is_skip_holiday is not None else False
    )

    if use_local_time_zone:
        # TODO: Implement local timezone logic
        pass
    default_schedule = get_default_schedule(db, current_user.team_id)
    schedule = SequenceCampaignSchedule(
        name=request.name,
        time_zone=time_zone.value,
        is_skip_holiday=is_skip_holiday,
        use_local_time_zone=use_local_time_zone,
        is_default=False if default_schedule else True,
        team_id=current_user.team_id,
        created_at=datetime.now(),
        created_by=current_user.id,
        updated_at=datetime.now(),
        updated_by=current_user.id,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    sending_windows = request.sending_windows
    windows = []
    days_list = set()
    if sending_windows:
        for window in sending_windows:
            days_list.add(window.week_day)
            sending_window = SequenceCampaignScheduleSendingWindows(
                schedule_id=schedule.id,
                start_time=window.start_time,
                end_time=window.end_time,
                week_day=window.week_day,
                created_by=current_user.id,
                updated_by=current_user.id,
            )
            windows.append(sending_window)
    db.add_all(windows)
    schedule.days_per_week = list(days_list)
    db.commit()
    db.refresh(schedule)
    return ScheduleBase(**schedule.dict(), sending_windows=sending_windows)
