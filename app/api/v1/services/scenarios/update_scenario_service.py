import i18n
from sqlmodel import Session, select

import app.api.v1.services.base_service as base_service
from app.api.base.exceptions import ForbiddenException, NotFoundException
from app.api.v1.schemas.scenarios import UpdateScenarioRequest
from app.api.v1.schemas.users import UserBase
from app.models.scenario import Scenario


def update_scenario(
    id: int, request: UpdateScenarioRequest, db: Session, current_user: UserBase
):
    scenario = db.exec(
        select(Scenario)
        .where(Scenario.team_id == current_user.team_id)
        .where(Scenario.id == id)
    ).first()
    if scenario is None:
        raise NotFoundException(detail=i18n.t("common.notFound"))

    remaining_active_scenario = base_service.remaining_active_scenario(
        db, current_user.team_id
    )

    if not scenario.email_notification_flag and not scenario.slack_notification_flag:
        if remaining_active_scenario <= 0 and (
            (request["email_notification_flag"] is True)
            or (request["slack_notification_flag"] is True)
        ):
            raise ForbiddenException(detail=i18n.t("company.maxScenatioActive"))

    for attr, value in request.items():
        if value is not None:
            setattr(scenario, attr, value)

    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario.id
