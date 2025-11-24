from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.models import TrackingUrl
from app.models.url_click_history import UrlClickHistory
from utils.hashids import get_hashids


def handle_click(db: Session, hashed_text: str):
    ids = get_hashids().decode(hashed_text)
    if len(ids) == 0:
        raise NotFoundException(detail="TrackingUrl.NotFound")
    tracking_url_id = ids[0]
    origin_url = db.exec(
        select(TrackingUrl.original_url).where(TrackingUrl.id == tracking_url_id)
    ).first()
    if not origin_url:
        raise NotFoundException(detail="TrackingUrl.NotFound")
    if len(ids) == 2:
        url_click_history = UrlClickHistory(
            tracking_url_id=tracking_url_id, corporate_number=str(ids[1])
        )
        db.add(url_click_history)
        db.commit()
    return RedirectResponse(origin_url)
