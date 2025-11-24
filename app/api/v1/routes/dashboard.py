from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.dashboard import DashBoardResponse
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.dashboard import (
    get_company_downloaded_service,
    get_sent_forms_service,
)

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("", response_model=DashBoardResponse)
def get_information_dashboard(
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    count_month_downloaded = (
        get_company_downloaded_service.count_this_month_downloaded_companies(
            db, current_user
        )
    )
    total_download = get_company_downloaded_service.count_total_downloaded_companies(
        db, current_user
    )
    count_month_sent_forms = get_sent_forms_service.count_this_month_sent_forms(
        db, current_user
    )

    total_sent_forms = get_sent_forms_service.count_total_sent_forms(db, current_user)
    return DashBoardResponse(
        count_month_downloaded=count_month_downloaded,
        total_downloaded=total_download,
        count_month_sent_forms=count_month_sent_forms,
        total_sent_forms=total_sent_forms,
    )
