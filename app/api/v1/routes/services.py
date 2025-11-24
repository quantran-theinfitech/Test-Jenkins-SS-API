from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

import app.api.v1.services.services as services
from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user, get_plan_code
from app.api.v1.schemas.services import GetServiceResponse
from app.api.v1.schemas.users import UserBase
from app.models.team import PlanCode

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get(
    "/listing-by-corporate_number/{corporate_number}",
    response_model=GetServiceResponse,
)
def listing_service_by_corporate_number(
    corporate_number: str,
    db: Session = Depends(get_session),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    current_user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    (
        services_result,
        total,
        unlimited_total,
    ) = services.listing_service_by_corporate_number(
        corporate_number, db, per_page, page, current_user, listing_plan_code
    )
    return GetServiceResponse(
        data=services_result, total=total, unlimited_total=unlimited_total
    )
