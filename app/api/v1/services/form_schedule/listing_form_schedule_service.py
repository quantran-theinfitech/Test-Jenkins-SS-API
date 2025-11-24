from typing import List, Optional

from sqlmodel import Session, asc, func, select

from app.api.v1.schemas.form_schedule import (
    DefaultFormScheduleRequest,
    FormScheduleItem,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.form_schedule.create_form_schedule_service import (
    create_form_schedule,
)
from app.models.form_schedule import FormSchedule


def listing_form_schedules(
    db: Session,
    current_user: UserBase,
    per_page: Optional[int],
    page: Optional[int],
) -> List[FormScheduleItem]:

    query = (
        select(FormSchedule)
        .where(
            FormSchedule.team_id == current_user.team_id,
            FormSchedule.deleted_at.is_(None),
        )
        .order_by(asc(FormSchedule.created_at), asc(FormSchedule.id))
    )

    # if page is not None and per_page is not None:
    #     query = query.offset((page - 1) * per_page)
    #     query = query.limit(per_page)

    form_schedules = db.exec(query).all()

    if len(form_schedules) == 0:
        return [create_form_schedule(db, current_user, DefaultFormScheduleRequest())]
    return [
        FormScheduleItem(**form_schedule.dict()) for form_schedule in form_schedules
    ]


def count_listing_form_schedules(
    db: Session,
    current_user: UserBase,
) -> int:
    query = select(func.count(FormSchedule.id)).where(
        FormSchedule.team_id == current_user.team_id,
        FormSchedule.deleted_at.is_(None),
    )
    count = db.exec(query).one()
    return count
