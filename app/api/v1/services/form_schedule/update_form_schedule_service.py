from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlmodel import Session, func, select, update

from app.api.base.exceptions import BadRequestException, NotFoundException
from app.api.v1.schemas.form_schedule import FormScheduleItem, UpdateFormScheduleRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.form_schedule.get_form_schedule_detail_service import (
    get_default_form_schedule,
)
from app.models.form_schedule import FormSchedule
from app.models.form_schedule_sending_window import FormScheduleSendingWindow


def update_form_schedule(
    db: Session,
    current_user: UserBase,
    form_schedule_id: int,
    request: UpdateFormScheduleRequest,
):
    detail_schedule = db.exec(
        select(FormSchedule).where(
            FormSchedule.id == form_schedule_id,
            FormSchedule.team_id == current_user.team_id,
            FormSchedule.deleted_at.is_(None),
        )
    ).first()

    if not detail_schedule:
        raise NotFoundException(
            detail="form_schedule.formScheduleNotFound",
        )

    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == "name":
            if not value:
                raise BadRequestException("form_schedule.nameIsRequired")
            if len(value) > 256:
                raise BadRequestException("form_schedule.nameIsTooLong")
            name_exists = (
                db.query(FormSchedule)
                .filter(
                    FormSchedule.name == value,
                    FormSchedule.deleted_at.is_(None),
                    FormSchedule.team_id == current_user.team_id,
                    FormSchedule.id != form_schedule_id,
                )
                .first()
            )
            if name_exists:
                raise BadRequestException("form_schedule.duplicateName")
            else:
                setattr(detail_schedule, key, value)
        elif key == "is_default":
            return mark_default_form_schedule_service(
                db, current_user.id, current_user.team_id, form_schedule_id, value
            )
        elif key == "sending_windows":
            if not value:
                raise BadRequestException(detail="form_schedule.emptySendingWindows")
            for window in value:
                if window["start_time"] > window["end_time"]:
                    raise BadRequestException(detail="form_schedule.timeIsInvalid")
            update_form_schedule_sending_windows(
                db,
                form_schedule_id,
                current_user.id,
                value,
            )
            days_per_week = db.exec(
                select(func.distinct(FormScheduleSendingWindow.week_day))
                .where(
                    FormScheduleSendingWindow.form_schedule_id == form_schedule_id,
                    FormScheduleSendingWindow.deleted_at.is_(None),
                )
                .order_by(FormScheduleSendingWindow.week_day)
            ).all()
            detail_schedule.days_per_week = days_per_week
        else:
            setattr(detail_schedule, key, value)
    detail_schedule.updated_at = datetime.now()
    detail_schedule.updated_by = current_user.id
    db.add(detail_schedule)
    db.commit()
    db.refresh(detail_schedule)
    sending_windows = db.exec(
        select(
            FormScheduleSendingWindow.week_day,
            FormScheduleSendingWindow.start_time,
            FormScheduleSendingWindow.end_time,
        )
        .where(
            FormScheduleSendingWindow.form_schedule_id == form_schedule_id,
            FormScheduleSendingWindow.deleted_at.is_(None),
        )
        .order_by(FormScheduleSendingWindow.week_day)
    ).all()
    return FormScheduleItem(
        **detail_schedule.dict(),
        sending_windows=sending_windows,
    )


def mark_default_form_schedule_service(
    db: Session, user_id: int, team_id: int, form_schedule_id: int, value: bool = True
):
    schedule = db.exec(
        select(FormSchedule).where(
            FormSchedule.id == form_schedule_id,
            FormSchedule.deleted_at.is_(None),
            FormSchedule.team_id == team_id,
        )
    ).first()
    if not schedule:
        raise NotFoundException(detail="form_schedule.formScheduleNotFound")

    if schedule.is_default:
        return FormScheduleItem(**schedule.dict())
    else:
        default_schedule = get_default_form_schedule(db, team_id)
        if default_schedule:
            default_schedule.is_default = False
            default_schedule.updated_at = datetime.now()
            default_schedule.updated_by = user_id
            db.add(default_schedule)
        query = (
            update(FormSchedule)
            .where(
                FormSchedule.id == form_schedule_id,
                FormSchedule.deleted_at.is_(None),
                FormSchedule.team_id == team_id,
                FormSchedule.is_default.is_not(value),
            )
            .values(is_default=value, updated_at=datetime.now(), updated_by=user_id)
        )
        db.exec(query)
        db.commit()
        return get_default_form_schedule(db, team_id)


def update_form_schedule_sending_windows(
    db: Session,
    form_schedule_id: int,
    user_id: int,
    windows: Optional[List[Dict[str, Any]]] = None,
):
    stmt = select(FormScheduleSendingWindow).where(
        FormScheduleSendingWindow.form_schedule_id == form_schedule_id,
        FormScheduleSendingWindow.deleted_at.is_(None),
    )
    existing_windows = db.exec(stmt).all()

    for window in existing_windows:
        window.deleted_at = datetime.now()
        window.deleted_by = user_id
        db.add(window)
    for window in windows:
        update_window = FormScheduleSendingWindow(
            form_schedule_id=form_schedule_id,
            start_time=window["start_time"],
            end_time=window["end_time"],
            week_day=window["week_day"],
            created_by=user_id,
            updated_by=user_id,
            updated_at=datetime.now(),
        )
        db.add(update_window)
    db.commit()
