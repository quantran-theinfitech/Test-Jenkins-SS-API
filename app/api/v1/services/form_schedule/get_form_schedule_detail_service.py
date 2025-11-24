from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.form_schedule import FormScheduleItem
from app.api.v1.schemas.users import UserBase
from app.models.form_schedule import FormSchedule
from app.models.form_schedule_sending_window import FormScheduleSendingWindow


def get_form_schedule_detail(
    db: Session,
    current_user: UserBase,
    form_schedule_id: int,
) -> FormScheduleItem:
    query = select(FormSchedule).where(
        FormSchedule.id == form_schedule_id,
        FormSchedule.team_id == current_user.team_id,
        FormSchedule.deleted_at.is_(None),
    )
    form_schedule_detail = db.exec(query).first()

    if not form_schedule_detail:
        raise NotFoundException(
            detail="form_schedule.formScheduleNotFound",
        )

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
        **form_schedule_detail.dict(),
        sending_windows=sending_windows,
    )


def get_default_form_schedule(
    db: Session,
    team_id: int,
):
    query = select(FormSchedule).where(
        FormSchedule.is_default.is_(True),
        FormSchedule.team_id == team_id,
        FormSchedule.deleted_at.is_(None),
    )
    return db.exec(query).first()
