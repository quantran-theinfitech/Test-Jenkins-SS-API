from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.credits import CreditsStatusResponse
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.credits import get_credit_status_service

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/usage", response_model=List[CreditsStatusResponse])
def usage_credit(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    credit_status = get_credit_status_service.get_credit_status(
        db, current_user.team_id
    )

    return credit_status
