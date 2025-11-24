from fastapi import APIRouter, Depends
from sqlmodel import Session

import app.api.v1.services.tracking_urls as tracking_url_service
from app.api.base.deps import custom_generate_unique_id, get_session

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/{hashed_text}", response_model=int)
def handle_click(
    hashed_text: str,
    db: Session = Depends(get_session),
):
    return tracking_url_service.handle_click(db, hashed_text)
