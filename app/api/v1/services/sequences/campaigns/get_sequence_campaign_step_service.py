from math import floor
from typing import List

from sqlmodel import Session, asc, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.mail_histories.verify_campaign_permisstion_service import (
    verify_campaign_permission,
)
from app.models.sequence.step import ScheduleUnit, SequenceCampaignStep, TimingType


def get_total_days_count(steps: List[SequenceCampaignStep]):
    total_days = 1
    for step in steps:
        if step.timing_type == TimingType.SCHEDULED:
            if step.schedule_unit == ScheduleUnit.DAYS:
                total_days = total_days + step.schedule_value
            if step.schedule_unit == ScheduleUnit.HOURS:
                total_days = total_days + (step.schedule_value / 24)
            if step.schedule_unit == ScheduleUnit.MINUTES:
                total_days = total_days + (step.schedule_value / (24 * 60))
    return floor(total_days)


def get_listing_step_service(
    campaign_id: int,
    db: Session,
    current_user: UserBase,
):
    try:
        verify_campaign_permission(db, current_user, campaign_id)
        query = (
            select(SequenceCampaignStep)
            .where(
                SequenceCampaignStep.deleted_at.is_(None),
                SequenceCampaignStep.sequence_campaign_id == campaign_id,
            )
            .order_by(asc(SequenceCampaignStep.order))
        )
        results = db.exec(query).all()
        return [result for result in results]
    except Exception as e:
        db.rollback()
        raise e


def get_detail_step_service(
    db: Session,
    step_id: int,
):
    query = select(SequenceCampaignStep).where(
        SequenceCampaignStep.deleted_at.is_(None),
        SequenceCampaignStep.id == step_id,
    )
    result = db.exec(query).first()
    if not result:
        raise NotFoundException("Step not found")
    ret = dict(result)
    ret["statistic"] = {
        "scheduled_count": 0,
        "delivered_count": 0,
        "bounced_count": 0,
        "spam_blocked_count": 0,
        "reply_count": 0,
        "interested_count": 0,
        "opt_out_count": 0,
        "open_count": 0,
    }
    return ret
