import json

import i18n
import requests
from sqlalchemy.sql.operators import is_
from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.connections import SlackConnectionResponse
from app.api.v1.schemas.users import UserBase
from app.config import settings
from app.models.scenario import Scenario
from app.models.slack_connection import SlackConnection


def create_slack_connection(
    authentication_code: str, db: Session, current_user: UserBase
) -> SlackConnectionResponse:
    auth_data = {
        "code": authentication_code,
        "client_id": settings.CLIENT_ID,
        "client_secret": settings.CLIENT_SECRET,
    }
    response = requests.post(settings.SLACK_HOST, data=auth_data)
    response_data = json.loads(response.text)
    try:
        if response_data["scope"] == "incoming-webhook":
            workspace_id = response_data["team"]["id"]
            workspace_name = response_data["team"]["name"]
            channel_id = response_data["incoming_webhook"]["channel_id"]
            channel_name = response_data["incoming_webhook"]["channel"]
            url = response_data["incoming_webhook"]["url"]
            slack_connection = SlackConnection(
                team_id=current_user.team_id,
                workspace_id=workspace_id,
                workspace_name=workspace_name,
                channel_id=channel_id,
                channel_name=channel_name,
                url=url,
            )
            db.add(slack_connection)
            db.commit()
            db.refresh(slack_connection)
            return SlackConnectionResponse(
                workspace_id=workspace_id,
                workspace_name=workspace_name,
                channel_id=channel_id,
                channel_name=channel_name,
                url=url,
                status=True,
            )
        return SlackConnectionResponse(status=False)
    except Exception:
        return SlackConnectionResponse(status=False)


def delete_slack_connection(connection_id: int, db: Session, current_user: UserBase):
    slack_connection = db.exec(
        select(SlackConnection)
        .join(
            Scenario,
            Scenario.target_slack_connection_id == SlackConnection.id,
            isouter=True,
        )
        .where(is_(Scenario.id, None))
        .where(SlackConnection.id == connection_id)
        .where(SlackConnection.team_id == current_user.team_id)
    ).one()
    if not slack_connection:
        raise NotFoundException(i18n.t("common.notFound"))
    db.delete(slack_connection)
    db.commit()
    return slack_connection.id
