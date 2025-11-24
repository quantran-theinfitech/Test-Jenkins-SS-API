from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.v1.schemas.sequence.campaign_settings import (
    SequenceCampaignSettingResponse,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.schedules.get_detail_schedules_services import (
    get_detail_schedule_service,
)
from app.api.v1.services.sequences.schedules.listing_schedules_service import (
    listing_schedules_service,
)
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_setting import SequenceCampaignSetting
from app.models.user import User

from .create_sequence_campaign_setting_service import (
    create_sequence_campaign_default_setting_service,
)


def get_campaign_setting_service(
    campaign_id: int,
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
            SequenceCampaign.deleted_at.is_(None),
        )
    )
    result = db.exec(query).first()
    if not result:
        raise HTTPException(status_code=400, detail="common.notFound")

    campaign, setting = result
    if not setting:
        setting = create_sequence_campaign_default_setting_service(campaign.id, db)
    schedule = get_detail_schedule_service(campaign.schedule_id, db, current_user)
    schedule_list = listing_schedules_service(db, current_user, 0, 0)
    sequence_owner = None
    is_owner_current_user = None
    if campaign.owner_id != current_user.id:
        sequence_owner = db.exec(
            select(User.name).where(User.id == campaign.owner_id)
        ).first()
        is_owner_current_user = False
    else:
        sequence_owner = current_user.name
        is_owner_current_user = True
    return SequenceCampaignSettingResponse(
        sequence_campaign_name=campaign.name,
        sequence_campaign_owner=sequence_owner,
        sequence_schedule=schedule,
        is_owner_current_user=is_owner_current_user,
        **setting.dict(),
        sequence_schedule_list=schedule_list,
    )
