from json import dumps, loads

import i18n
from sqlmodel import Session

from app.api.base.exceptions import ForbiddenException
from app.api.v1.schemas.scenarios import ScenarioSettingRequest
from app.api.v1.schemas.search_press_releases import SearchPressReleaseRequest
from app.api.v1.schemas.search_recruits import SearchRecruitRequest
from app.models.scenario import Scenario
from app.models.team import PlanCode
from app.models.user import User


def create_scenario_setting(
    request: ScenarioSettingRequest,
    db: Session,
    current_user: User,
    listing_plan_code: PlanCode,
):
    if listing_plan_code != PlanCode.UNLIMITED:
        raise ForbiddenException(detail=i18n.t("auth.permissionDenied"))
    if request.type_code == "RECRUIT":
        trigger_conditions = (
            SearchRecruitRequest()  # type: ignore
            if request.trigger_conditions is None
            else request.trigger_conditions
        )
    elif request.type_code == "NEWS":
        trigger_conditions = (
            SearchPressReleaseRequest()  # type: ignore
            if request.trigger_conditions is None
            else request.trigger_conditions
        )
    scenario = Scenario(
        name=request.name,
        description=request.description,
        trigger_conditions=loads(dumps(trigger_conditions.dict(), default=str)),
        target_email=request.target_email,
        target_slack_connection_id=request.target_slack_connection_id,
        team_id=current_user.team_id,
        created_by=current_user.id,
        type_code=request.type_code,  # type: ignore
        email_notification_flag=request.email_notification_flag,
        slack_notification_flag=request.slack_notification_flag,
    )
    db.add(scenario)
    db.flush()
    db.refresh(scenario)
    db.commit()
    return scenario.id
