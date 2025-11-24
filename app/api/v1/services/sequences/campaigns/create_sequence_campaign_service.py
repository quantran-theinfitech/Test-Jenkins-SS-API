from sqlmodel import Session

from app.api.v1.schemas.sequence.campaigns import CreateCampaignRequest, SequenceBase
from app.api.v1.schemas.users import UserBase
from app.models.sequence.campaign import SequenceCampaign


def create_campaign_service(
    db: Session, request: CreateCampaignRequest, current_user: UserBase
):
    try:
        campaign = SequenceCampaign(
            name=request.name,
            team_id=current_user.team_id,
            created_by=current_user.id,
            updated_by=current_user.id,
            owner_id=current_user.id,
            schedule_id=request.schedule_id,
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return SequenceBase(**campaign.dict())
    except Exception as e:
        db.rollback()
        raise e
