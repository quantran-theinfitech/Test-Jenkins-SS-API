from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.hubspot_connections import HubspotCreateFieldRequest
from app.api.v1.schemas.users import UserBase
from app.models.integration.hubspot.hubspot_integrations import HubspotIntergrations
from utils.hubspot_connection import HubSpotService


def create_hubspot_field(
    db: Session,
    current_user: UserBase,
    request: HubspotCreateFieldRequest,
):
    try:

        hubspot_connection = db.exec(
            select(HubspotIntergrations).where(
                HubspotIntergrations.team_id == current_user.team_id,
                HubspotIntergrations.deleted_at.is_(None),
            )
        ).first()

        if not hubspot_connection:
            raise NotFoundException(detail="integration.hubspot.notFoundConnection")

        hubspot_service = HubSpotService(
            access_token=hubspot_connection.access_token,
            refresh_token=hubspot_connection.refresh_token,
        )

        if request and len(request.custom_field) > 0:
            for field in request.custom_field:
                hubspot_service.create_custom_field(
                    name=field.name if field.name is not None else "",
                    label=field.label if field.label is not None else "",
                    type=field.type_field if field.type_field is not None else "string",
                )
        return 1
    except HTTPException as e:
        raise e
