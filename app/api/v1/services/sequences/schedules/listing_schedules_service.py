from sqlalchemy import asc, func
from sqlmodel import Session, select

from app.api.v1.schemas.sequence.schedules import DefaultScheduleRequest, ScheduleBase
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.schedules.create_schedule_service import (
    create_schedule_service,
)
from app.models.sequence.schedule import SequenceCampaignSchedule


def listing_schedules_service(
    db: Session,
    current_user: UserBase,
    per_page: int,
    page: int,
):
    condition = [
        SequenceCampaignSchedule.team_id == current_user.team_id,
        SequenceCampaignSchedule.deleted_at.is_(None),
    ]
    query = (
        select(SequenceCampaignSchedule)
        .where(*condition)
        .order_by(
            asc(SequenceCampaignSchedule.created_at), asc(SequenceCampaignSchedule.id)
        )
    )
    schedules = db.exec(query).all()
    if len(schedules) == 0:
        return [create_schedule_service(db, current_user, DefaultScheduleRequest())]
    return [ScheduleBase(**schedule.dict()) for schedule in schedules]


def count_listing_schedules_service(
    db: Session,
    current_user: UserBase,
):
    condition = [
        SequenceCampaignSchedule.team_id == current_user.team_id,
        SequenceCampaignSchedule.deleted_at.is_(None),
    ]
    query = select(func.count(SequenceCampaignSchedule.id)).where(*condition)
    count = db.exec(query).one()
    return count
