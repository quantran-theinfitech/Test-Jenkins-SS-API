from sqlmodel import Session

from app.api.v1.schemas.tracking_urls import CreateTrackingUrlRequest
from app.api.v1.schemas.users import UserBase
from app.models import TrackingUrl
from utils.hashids import get_hashids


def create_tracking_url(
    db: Session, current_user: UserBase, request: CreateTrackingUrlRequest
):
    tracking_url = TrackingUrl(
        team_id=current_user.team_id,
        name=request.name,
        original_url=request.original_url,
        tracking_flag=request.tracking_flag,
        created_by=current_user.id,
    )
    db.add(tracking_url)
    db.flush()
    db.refresh(tracking_url)
    tracking_url.shorten_path = get_hashids().encode(tracking_url.id)
    db.add(tracking_url)
    db.commit()
    db.refresh(tracking_url)
    return tracking_url
