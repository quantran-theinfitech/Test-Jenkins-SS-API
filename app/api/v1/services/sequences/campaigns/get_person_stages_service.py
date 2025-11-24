from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.models.sequence.campaign import SequenceCampaign
from app.api.v1.schemas.users import UserBase


def get_person_stages_service(db: Session, current_user: UserBase, campaign_id: int):
    campaign = db.exec(
        select(SequenceCampaign).where(
            SequenceCampaign.id == campaign_id,
            SequenceCampaign.deleted_at.is_(None),
            SequenceCampaign.team_id == current_user.team_id,
        )
    ).scalar_one_or_none()

    if not campaign:
        raise NotFoundException("Campaign not found")

    person_stages = {
        "total": 100,
        "new": 20,
        "open": 15,
        "in_progress": 30,
        "open_deal": 10,
        "unqualified": 5,
        "attempted_to_contacts": 8,
        "connected": 7,
        "bad_timing": 3,
        "no_stage": 2,
        "all_in_progress_stages": 45,
        "all_succeeded_stages": 35,
        "all_failed_stages": 20,
    }
    return person_stages
