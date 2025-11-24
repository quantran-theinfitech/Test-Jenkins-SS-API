from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.v1.schemas.sequence.campaign_settings import (
    SequenceCampaignSettingBase,
    UpdateCampaignSettingRequest,
)
from app.api.v1.schemas.users import UserBase
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_setting import SequenceCampaignSetting
from app.models.sequence.schedule import SequenceCampaignSchedule

from .create_sequence_campaign_setting_service import (
    create_sequence_campaign_default_setting_service,
)


def update_campaign_setting_service(
    campaign_id: int,
    request: UpdateCampaignSettingRequest,
    db: Session,
    current_user: UserBase,
):
    query = (
        select(
            SequenceCampaign,
            SequenceCampaignSetting,
        )
        .join(
            SequenceCampaignSetting,
            SequenceCampaignSetting.sequence_campaign_id == SequenceCampaign.id,
            isouter=True,
        )
        .where(
            SequenceCampaign.id == campaign_id,
            SequenceCampaign.owner_id == current_user.id,
            SequenceCampaign.deleted_at.is_(None),
        )
    )
    result = db.exec(query).first()
    if not result:
        raise HTTPException(status_code=400, detail="common.notFound")

    campaign, setting = result
    if not setting:
        setting = create_sequence_campaign_default_setting_service(campaign.id, db)
    if request.sequence_schedule_id:
        schedule_id = request.sequence_schedule_id
        condition = [
            SequenceCampaignSchedule.id == schedule_id,
            SequenceCampaignSchedule.team_id == current_user.team_id,
            SequenceCampaignSchedule.deleted_at.is_(None),
        ]
        query = select(SequenceCampaignSchedule).where(*condition)
        schedule = db.exec(query).one_or_none()
        if schedule is None:
            raise HTTPException(status_code=404, detail="sequence.scheduleNotFound")
        schedule_id = schedule.id
        campaign.schedule_id = schedule_id
        campaign.updated_at = datetime.now()
        db.add(campaign)
    if request.sequence_name:
        campaign.name = request.sequence_name
        campaign.updated_at = datetime.now()
        db.add(campaign)
    if request.days_until_unresponsive is None:
        setting.days_until_unresponsive = None
    for attr, value in request.dict(exclude_unset=True).items():
        if hasattr(setting, attr):
            setattr(setting, attr, value)
    setting.updated_by = current_user.id
    setting.updated_at = datetime.now()
    db.add(setting)
    db.commit()
    db.refresh(campaign)
    db.refresh(setting)
    return SequenceCampaignSettingBase(
        sequence_campaign_name=campaign.name,
        sequence_campaign_owner=current_user.name,
        **setting.dict(),
    )
