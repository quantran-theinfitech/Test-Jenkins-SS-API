from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select, update

from app.api.v1.schemas.sequence.schedules import DeleteScheduleRequest
from app.api.v1.schemas.users import UserBase
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.schedule import SequenceCampaignSchedule
from app.models.sequence.schedule_sending_windows import (
    SequenceCampaignScheduleSendingWindows as SendingWindow,
)

from .get_detail_schedules_services import get_default_schedule
from .update_schedule_service import mark_default_schedule_service


def delete_schedule_service(
    db: Session,
    current_user: UserBase,
    schedule_id: int,
    request: DeleteScheduleRequest,
):
    default_schedule = get_default_schedule(db, current_user.team_id)
    if default_schedule:
        if schedule_id == default_schedule.id:
            if (
                not request.new_default_schedule_id
                or request.new_default_schedule_id == schedule_id
            ):
                raise HTTPException(
                    status_code=400, detail="sequence.canNotDeleteDefaultSchedule"
                )
    if schedule_id == request.new_default_schedule_id:
        raise HTTPException(
            status_code=400, detail="sequence.canNotAssignScheduleThatWillBeDeleted"
        )
    try:
        condition = [
            SequenceCampaignSchedule.id == schedule_id,
            SequenceCampaignSchedule.team_id == current_user.team_id,
            SequenceCampaignSchedule.deleted_at.is_(None),
        ]
        query = select(SequenceCampaignSchedule).where(*condition)
        schedule = db.exec(query).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="sequence.scheduleNotFound")
        schedule.deleted_at = datetime.now()
        schedule.deleted_by = current_user.id
        db.add(schedule)
        sending_windows = db.exec(
            select(SendingWindow).where(
                SendingWindow.schedule_id == schedule.id,
                SendingWindow.deleted_at.is_(None),
            )
        ).all()
        for window in sending_windows:
            window.deleted_at = datetime.now()
            window.deleted_by = current_user.id
            db.add(window)
        if (
            request.new_default_schedule_id
            and request.new_default_schedule_id != schedule_id
        ):
            mark_default_schedule_service(
                db,
                current_user.id,
                current_user.team_id,
                request.new_default_schedule_id,
                value=True,
            )
        db.exec(
            update(SequenceCampaign)
            .where(
                SequenceCampaign.schedule_id == schedule_id,
                SequenceCampaign.deleted_at.is_(None),
            )
            .values(schedule_id=request.new_default_schedule_id)
        )
        db.commit()
        db.refresh(schedule)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e
