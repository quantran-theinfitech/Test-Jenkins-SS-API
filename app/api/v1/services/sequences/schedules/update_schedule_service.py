from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import func, update
from sqlmodel import Session, select

from app.api.v1.schemas.sequence.schedules import ScheduleBase, UpdateScheduleRequest
from app.api.v1.schemas.users import UserBase
from app.models.sequence.schedule import SequenceCampaignSchedule
from app.models.sequence.schedule_sending_windows import (
    SequenceCampaignScheduleSendingWindows as SendingWindow,
)

from .get_detail_schedules_services import get_default_schedule


def get_schedule_by_id(
    db: Session, schedule_id: int, team_id: int
) -> SequenceCampaignSchedule:
    query = select(SequenceCampaignSchedule).where(
        SequenceCampaignSchedule.id == schedule_id,
        SequenceCampaignSchedule.team_id == team_id,
        SequenceCampaignSchedule.deleted_at.is_(None),
    )
    schedule = db.exec(query).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="sequence.scheduleNotFound")
    return schedule


def update_schedule_service(
    db: Session,
    current_user: UserBase,
    schedule_id: int,
    request: UpdateScheduleRequest,
):
    schedule = get_schedule_by_id(db, schedule_id, current_user.team_id)
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == "name":
            if not value:
                raise HTTPException(status_code=400, detail="sequence.nameIsRequired")
            if len(value) > 256:
                raise HTTPException(status_code=400, detail="sequence.nameIsTooLong")
            name_exists = (
                db.query(SequenceCampaignSchedule)
                .filter(
                    SequenceCampaignSchedule.name == value,
                    SequenceCampaignSchedule.deleted_at.is_(None),
                    SequenceCampaignSchedule.team_id == current_user.team_id,
                    SequenceCampaignSchedule.id != schedule_id,
                )
                .first()
            )
            if name_exists:
                raise HTTPException(status_code=400, detail="sequence.duplicateName")
            else:
                setattr(schedule, key, value)
        elif key == "is_default":
            return mark_default_schedule_service(
                db, current_user.id, current_user.team_id, schedule_id, value
            )
        elif key == "sending_windows":
            if not value:
                raise HTTPException(
                    status_code=400, detail="sequence.emptySendingWindows"
                )
            for window in value:
                if window["start_time"] > window["end_time"]:
                    raise HTTPException(
                        status_code=400, detail="sequence.TimeIsInvalid"
                    )
            update_sending_windows(db, schedule_id, current_user.id, value)
            days_per_week = db.exec(
                select(func.distinct(SendingWindow.week_day))
                .where(
                    SendingWindow.schedule_id == schedule_id,
                    SendingWindow.deleted_at.is_(None),
                )
                .order_by(SendingWindow.week_day)
            ).all()
            schedule.days_per_week = days_per_week
        else:
            setattr(schedule, key, value)
    schedule.updated_at = datetime.now()
    schedule.updated_by = current_user.id
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    sending_windows = db.exec(
        select(SendingWindow.week_day, SendingWindow.start_time, SendingWindow.end_time)
        .where(
            SendingWindow.schedule_id == schedule_id,
            SendingWindow.deleted_at.is_(None),
        )
        .order_by(SendingWindow.week_day)
    ).all()
    return ScheduleBase(**schedule.dict(), sending_windows=sending_windows)


def mark_default_schedule_service(
    db: Session, user_id: int, team_id: int, schedule_id: int, value: bool = True
):

    condition = [
        SequenceCampaignSchedule.id == schedule_id,
        SequenceCampaignSchedule.deleted_at.is_(None),
        SequenceCampaignSchedule.team_id == team_id,
    ]
    schedule = db.exec(select(SequenceCampaignSchedule).where(*condition)).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="sequence.scheduleNotFound")

    if schedule.is_default:
        return ScheduleBase(**schedule.dict())
    else:
        default_schedule = get_default_schedule(db, team_id)
        if default_schedule:
            default_schedule.is_default = False
            default_schedule.updated_at = datetime.now()
            default_schedule.updated_by = user_id
            db.add(default_schedule)
        query = (
            update(SequenceCampaignSchedule)
            .where(*condition, SequenceCampaignSchedule.is_default.is_not(value))
            .values(is_default=value, updated_at=datetime.now(), updated_by=user_id)
        )
        db.exec(query)
        db.commit()
        return get_default_schedule(db, team_id)


def update_sending_windows(
    db: Session,
    schedule_id: int,
    user_id: int,
    windows: Optional[List[Dict[str, Any]]] = None,
):
    stmt = select(SendingWindow).where(
        SendingWindow.schedule_id == schedule_id,
        SendingWindow.deleted_at.is_(None),
    )
    existing_windows = db.exec(stmt).all()

    for window in existing_windows:
        window.deleted_at = datetime.now()
        window.deleted_by = user_id
        db.add(window)
    for window in windows:
        update_window = SendingWindow(
            schedule_id=schedule_id,
            start_time=window["start_time"],
            end_time=window["end_time"],
            week_day=window["week_day"],
            created_by=user_id,
            updated_by=user_id,
            updated_at=datetime.now(),
        )
        db.add(update_window)
    db.commit()
