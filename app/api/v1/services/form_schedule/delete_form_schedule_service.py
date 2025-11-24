from datetime import datetime

from sqlmodel import Session, select, update

from app.api.base.exceptions import BadRequestException, NotFoundException
from app.api.v1.schemas.form_schedule import DeleteFormScheduleRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.form_schedule.get_form_schedule_detail_service import (
    get_default_form_schedule,
)
from app.api.v1.services.form_schedule.update_form_schedule_service import (
    mark_default_form_schedule_service,
)
from app.models.form_job import FormJob
from app.models.form_schedule import FormSchedule
from app.models.form_schedule_sending_window import FormScheduleSendingWindow


def delete_form_schedule(
    db: Session,
    current_user: UserBase,
    form_schedule_id: int,
    request: DeleteFormScheduleRequest,
):
    default_schedule = get_default_form_schedule(db, current_user.team_id)
    if default_schedule:
        if form_schedule_id == default_schedule.id:
            if (
                not request.new_default_schedule_id
                or request.new_default_schedule_id == form_schedule_id
            ):
                raise BadRequestException(
                    detail="form_schedule.canNotDeleteDefaultSchedule"
                )

    try:
        query = select(FormSchedule).where(
            FormSchedule.id == form_schedule_id,
            FormSchedule.team_id == current_user.team_id,
            FormSchedule.deleted_at.is_(None),
        )
        form_schedule = db.exec(query).first()

        if not form_schedule:
            raise NotFoundException(detail="form_schedule.formScheduleNotFound")

        form_schedule.deleted_at = datetime.now()
        form_schedule.deleted_by = current_user.id
        db.add(form_schedule)

        form_schedule_sending_windows = db.exec(
            select(FormScheduleSendingWindow).where(
                FormScheduleSendingWindow.form_schedule_id == form_schedule.id,
                FormScheduleSendingWindow.deleted_at.is_(None),
            )
        ).all()

        for window in form_schedule_sending_windows:
            window.deleted_at = datetime.now()
            window.deleted_by = current_user.id
            db.add(window)

        if (
            request.new_default_schedule_id
            and request.new_default_schedule_id != form_schedule_id
        ):
            mark_default_form_schedule_service(
                db=db,
                user_id=current_user.id,
                team_id=current_user.team_id,
                form_schedule_id=request.new_default_schedule_id,
                value=True,
            )

        new_form_schedule_id = (
            request.new_default_schedule_id
            if form_schedule_id == default_schedule.id
            else default_schedule.id
        )

        query_update_form_job = (
            update(FormJob)
            .where(FormJob.form_schedule_id == form_schedule_id)
            .values(
                form_schedule_id=new_form_schedule_id,
                updated_at=datetime.now(),
                updated_by=current_user.id,
            )
        )
        db.execute(query_update_form_job)
        db.commit()
        db.refresh(form_schedule)
    except Exception as e:
        db.rollback()
        raise BadRequestException(detail=str(e)) from e
