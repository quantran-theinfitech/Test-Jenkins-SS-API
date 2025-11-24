from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.hubspot_connections import HubspotCompanySchemaResponse
from app.api.v1.schemas.users import UserBase
from app.models import HubspotIntergrations
from utils.hubspot_connection import HubSpotService


def listing_schema_company_hubspot(
    db: Session, current_user: UserBase
) -> HubspotCompanySchemaResponse:
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
    schema_company = hubspot_service.get_schema_company()

    response = [
        {
            "name": property.name,
            "label": property.label,
            "type_field": property.type,
            "group": property.group_name,
        }
        for property in schema_company
    ]

    return HubspotCompanySchemaResponse(
        connection_id=hubspot_connection.id, data=response
    )
