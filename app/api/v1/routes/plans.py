from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.plans import (
    PlanDetailResponse,
    PlanHistory,
    PlanHistoryResponse,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.plans import get_plan_detail_service, get_plan_history_service

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("", response_model=PlanDetailResponse)
def plan_detail(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    plan_detail = get_plan_detail_service.get_plan_detail(db, current_user.team_id)

    return PlanDetailResponse(
        name_code=plan_detail.name_code,
        unlock_cpn_quota=plan_detail.unlock_cpn_quota,
        send_form_quota=plan_detail.send_form_quota,
        max_active_scenarios_number=plan_detail.max_active_scenarios_number,
        unlock_person_quota=plan_detail.unlock_person_quota,
        send_email_quota=plan_detail.send_email_quota,
        download_csv_quota=plan_detail.download_csv_quota,
        telesale_quota=plan_detail.telesale_quota,
        price=plan_detail.price,
        contract_month=plan_detail.contract_month,
        start_at=plan_detail.start_at,
        expire_at=plan_detail.expire_at,
        linkedin_connect_quota=plan_detail.linkedin_connect_quota,
        linkedin_message_quota=plan_detail.linkedin_message_quota,
    )


@router.get("/histories", response_model=PlanHistoryResponse)
def plan_histories(
    per_page: Optional[int] = Query(default=10, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    plan_histories = get_plan_history_service.get_plan_histories(
        db, current_user.team_id, page, per_page
    )

    total = get_plan_history_service.get_plan_history_count(db, current_user.team_id)

    return PlanHistoryResponse(
        page=page,
        per_page=per_page,
        total=total,
        data=[
            PlanHistory(
                name_code=plan_history.name_code,
                unlock_cpn_quota=plan_history.unlock_cpn_quota,
                send_form_quota=plan_history.send_form_quota,
                max_active_scenarios_number=plan_history.max_active_scenarios_number,
                unlock_person_quota=plan_history.unlock_person_quota,
                send_email_quota=plan_history.send_email_quota,
                download_csv_quota=plan_history.download_csv_quota,
                telesale_quota=plan_history.telesale_quota,
                price=plan_history.price,
                contract_month=plan_history.contract_month,
                start_at=plan_history.start_at,
                expire_at=plan_history.expire_at,
                is_active=plan_history.is_active,
                service_code=plan_history.service_code,
            )
            for plan_history in plan_histories
        ],
    )
