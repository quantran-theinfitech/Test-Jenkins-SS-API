from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.v1.schemas.sequence.schedules import ScheduleBase
from app.api.v1.schemas.users import UserBase
from app.models.sequence.schedule import SequenceCampaignSchedule
from app.models.sequence.schedule_sending_windows import (
    SequenceCampaignScheduleSendingWindows as SendingWindow,
)


def get_detail_schedule_service(
    schedule_id: int,
    db: Session,
    current_user: UserBase,
):
    condition = [
        SequenceCampaignSchedule.id == schedule_id,
        SequenceCampaignSchedule.team_id == current_user.team_id,
        SequenceCampaignSchedule.deleted_at.is_(None),
    ]
    query = select(SequenceCampaignSchedule).where(*condition)
    schedule = db.exec(query).one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="sequence.scheduleNotFound")

    sending_windows = db.exec(
        select(SendingWindow.week_day, SendingWindow.start_time, SendingWindow.end_time)
        .where(
            SendingWindow.schedule_id == schedule.id,
            SendingWindow.deleted_at.is_(None),
        )
        .order_by(SendingWindow.week_day)
    ).all()
    return ScheduleBase(
        **schedule.dict(),
        sending_windows=sending_windows,
        is_current_user=True if current_user.id == schedule.created_by else False,
    )


def get_default_schedule(
    db: Session,
    team_id: int,
):
    query = select(SequenceCampaignSchedule).where(
        SequenceCampaignSchedule.is_default.is_(True),
        SequenceCampaignSchedule.team_id == team_id,
        SequenceCampaignSchedule.deleted_at.is_(None),
    )
    return db.exec(query).first()
