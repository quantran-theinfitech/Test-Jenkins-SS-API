from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response
from sqlmodel import Session

import app.api.v1.services.base_service as base_service
import app.api.v1.services.scenarios as scenarios
from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.base.exceptions import ForbiddenException, PaymentRequiredException
from app.api.v1.dependencies import get_current_user, get_plan_code
from app.api.v1.dependencies.authentication import get_message_from_token
from app.api.v1.schemas.scenarios import (
    ListingScenarioNotificationItemsResponse,
    ScenarioDetailResponse,
    ScenarioManagementResponse,
    ScenarioNotificationResponse,
    ScenarioSettingRequest,
    SearchScenarioResponse,
    UpdateScenarioRequest,
)
from app.api.v1.schemas.users import UserBase
from app.models.scenario import TypeCode
from app.models.team import PlanCode
from app.models.user import User

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.post("/setting", response_model=int)
def create_scenario_setting(
    request: ScenarioSettingRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    remaining_active_scenario = base_service.remaining_active_scenario(
        db, current_user.team_id
    )
    if remaining_active_scenario <= 0:
        raise PaymentRequiredException()
    return scenarios.create_scenario_setting(
        request, db, current_user, listing_plan_code
    )


@router.get("/managements", response_model=ScenarioManagementResponse)
def listing_scenario_managements(
    db: Session = Depends(get_session),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    current_user: User = Depends(get_current_user()),
):
    listing_scenarios = scenarios.listing_scenario_managements(
        db, per_page, page, current_user.team_id
    )
    total = scenarios.listing_scenario_managements_count(db, current_user.team_id)
    return ScenarioManagementResponse(
        page=page, per_page=per_page, data=listing_scenarios, total=total
    )


@router.get("", response_model=List[SearchScenarioResponse])
def listing_scenarios(
    keyword: Optional[str] = None,
    type_code: Optional[TypeCode] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user()),
):
    return scenarios.listing_scenarios(db, current_user, keyword, type_code)


@router.get("/notify-new-recruit", response_model=bool)
def notify_new_recruit(
    verification_code: str = Depends(get_message_from_token()),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_session),
    code: str = Query(),
):
    if verification_code != code:
        raise ForbiddenException(detail="auth.permissionDenied")
    background_tasks.add_task(scenarios.notify_new_recruit, db)
    return True


@router.get("/notify-new-press-release", response_model=bool)
def notify_new_press_release(
    verification_code: str = Depends(get_message_from_token()),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_session),
    code: str = Query(),
):
    if verification_code != code:
        raise ForbiddenException(detail="auth.permissionDenied")
    background_tasks.add_task(scenarios.notify_new_press_release, db)
    return True


@router.get("/{id}", response_model=ScenarioDetailResponse)
def get_scenario_detail(
    id: int,
    db: Session = Depends(get_session),
    notification_id: Optional[int] = None,
    current_user: User = Depends(get_current_user()),
):
    scenario_detail = scenarios.get_scenario_detail(
        db, id, current_user.team_id, notification_id
    )
    return scenario_detail


@router.get("/{id}/notifications", response_model=ScenarioNotificationResponse)
def listing_scenario_notifications(
    id: int,
    db: Session = Depends(get_session),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    current_user: User = Depends(get_current_user()),
):
    listing_notifications = scenarios.listing_scenario_notifications(
        db, id, per_page, page, current_user.team_id
    )
    total = scenarios.listing_scenario_notifications_count(db, id, current_user.team_id)
    return ScenarioNotificationResponse(
        page=page, per_page=per_page, data=listing_notifications, total=total
    )


@router.get(
    "/notifications/{id}/items", response_model=ListingScenarioNotificationItemsResponse
)
def listing_scenario_notification_items(
    id: int,
    db: Session = Depends(get_session),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    current_user: User = Depends(get_current_user()),
):
    listing_items = scenarios.listing_scenario_notification_items(
        db, id, per_page, page, current_user.team_id
    )
    total = scenarios.listing_scenario_notification_items_count(db, id)
    return ListingScenarioNotificationItemsResponse(
        page=page, per_page=per_page, data=listing_items, total=total
    )


@router.patch("/{id}", response_model=int)
def update_scenario(
    id: int,
    request: UpdateScenarioRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return scenarios.update_scenario(
        id, request.dict(exclude_unset=True), db, current_user
    )


@router.delete("/{id}", status_code=HTTPStatus.NO_CONTENT, response_class=Response)
def delete_scenario(
    id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return scenarios.delete_scenario(id, db, current_user)
