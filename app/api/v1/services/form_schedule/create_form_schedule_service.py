from datetime import datetime

from sqlmodel import Session

from app.api.base.exceptions import BadRequestException
from app.api.v1.schemas.form_schedule import CreateFormScheduleRequest, FormScheduleItem
from app.api.v1.schemas.sequence.schedules import Timezone
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.schedules.create_schedule_service import (
    check_valid_sending_windows,
)
from app.models.form_schedule import FormSchedule
from app.models.form_schedule_sending_window import FormScheduleSendingWindow


def create_form_schedule(
    db: Session, current_user: UserBase, request: CreateFormScheduleRequest
) -> FormScheduleItem:
    if not check_valid_sending_windows(request.sending_windows):
        raise BadRequestException(detail="form_schedule.timeIsInvalid")
    if not request.name:
        raise BadRequestException(detail="form_schedule.nameIsRequired")

    is_name_exists = (
        db.query(FormSchedule)
        .filter(
            FormSchedule.name == request.name,
            FormSchedule.deleted_at.is_(None),
            FormSchedule.team_id == current_user.team_id,
        )
        .first()
    )

    if is_name_exists:
        raise BadRequestException(detail="form_schedule.duplicateName")

    if len(request.name) > 256:
        raise BadRequestException(detail="form_schedule.nameIsTooLong")

    time_zone = request.time_zone if request.time_zone else Timezone.JAPAN_STANDARD_TIME
    is_skip_holiday = (
        request.is_skip_holiday if request.is_skip_holiday is not None else False
    )

    default_schedule = (
        db.query(FormSchedule)
        .filter(
            FormSchedule.is_default.is_(True),
            FormSchedule.team_id == current_user.team_id,
            FormSchedule.deleted_at.is_(None),
        )
        .first()
    )

    form_schedule = FormSchedule(
        name=request.name,
        time_zone=time_zone,
        is_skip_holiday=is_skip_holiday,
        is_default=False if default_schedule else True,
        team_id=current_user.team_id,
        created_at=datetime.now(),
        created_by=current_user.id,
        updated_at=datetime.now(),
        updated_by=current_user.id,
    )

    db.add(form_schedule)
    db.commit()
    db.refresh(form_schedule)

    sending_windows = request.sending_windows
    windows = []
    days_list = set()
    if sending_windows:
        for window in sending_windows:
            days_list.add(window.week_day)
            sending_window = FormScheduleSendingWindow(
                form_schedule_id=form_schedule.id,
                start_time=window.start_time,
                end_time=window.end_time,
                week_day=window.week_day,
                created_by=current_user.id,
                updated_by=current_user.id,
            )
            windows.append(sending_window)
    db.add_all(windows)
    form_schedule.days_per_week = list(days_list)
    db.commit()
    db.refresh(form_schedule)
    return FormScheduleItem(**form_schedule.dict(), sending_windows=sending_windows)
