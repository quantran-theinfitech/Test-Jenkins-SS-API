from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.hubspot_connections import HubspotConnectionDetailResponse
from app.api.v1.schemas.users import UserBase
from app.models import HubspotIntergrations
from utils.hubspot_connection import HubSpotService


def hubspot_connection_detail(
    db: Session, current_user: UserBase
) -> HubspotConnectionDetailResponse:
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

    hubspot_service.refresh_client()

    return HubspotConnectionDetailResponse(
        hubspot_team_id=hubspot_connection.hubspot_team_id,
        email=hubspot_connection.email,
    )
