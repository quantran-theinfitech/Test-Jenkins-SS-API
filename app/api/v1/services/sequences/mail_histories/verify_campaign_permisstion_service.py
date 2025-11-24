from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.users import UserBase
from app.models.sequence.campaign import SequenceCampaign


def verify_campaign_permission(db: Session, current_user: UserBase, campaign_id: int):
    campaign = db.exec(
        select(SequenceCampaign).where(
            SequenceCampaign.id == campaign_id,
            SequenceCampaign.deleted_at.is_(None),
            SequenceCampaign.team_id == current_user.team_id,
        )
    ).first()
    if not campaign:
        raise NotFoundException("Campaign not found")
