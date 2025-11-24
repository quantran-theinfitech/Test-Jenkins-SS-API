from http import HTTPStatus

import i18n
from fastapi import Response
from sqlalchemy.sql import text
from sqlmodel import Session

from app.api.base.exceptions import ForbiddenException
from app.api.v1.schemas.users import UserBase


def delete_scenario(scenario_id: int, db: Session, current_user: UserBase):
    try:
        # Check permission of user
        isValidPermission = db.execute(
            text(
                f"""
                SELECT * FROM SCENARIOS
                WHERE id = {scenario_id} AND team_id = {current_user.team_id}
                """
            )
        ).first()

        if not isValidPermission:
            raise ForbiddenException(detail=i18n.t("auth.permissionDenied"))

        #  Filter and delete all sn items having sn_id listed in sn_id_list table.
        db.execute(
            text(
                f"""
            DELETE FROM scenario_notification_items sn_items
            USING scenario_notifications, scenarios
            WHERE sn_items.scenario_notification_id = scenario_notifications.id
                AND scenario_notifications.scenario_id = {scenario_id}
        """
            )
        )

        # Delete all scenario notification having its scenario_id = target scenario id
        db.execute(
            text(
                f"DELETE FROM scenario_notifications WHERE scenario_id = {scenario_id};"
            )
        )

        # Delete scenario having id = target id
        db.execute(text(f"DELETE FROM scenarios WHERE id = {scenario_id};"))

        db.commit()
        return Response(status_code=HTTPStatus.NO_CONTENT.value)

    except Exception as e:
        db.rollback()
        raise e
