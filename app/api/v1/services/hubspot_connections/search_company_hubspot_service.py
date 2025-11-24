from typing import Optional

from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.hubspot_connections import (
    SearchCompanyHubspot,
    SearchCompanyHubspotResponse,
)
from app.api.v1.schemas.users import UserBase
from app.models import HubspotIntergrations
from utils.hubspot_connection import HubSpotService


def search_company_hubspot(
    db: Session, current_user: UserBase, keyword: Optional[str] = None
) -> SearchCompanyHubspotResponse:
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
    companies = hubspot_service.search_company_hubpsot(
        keyword.lower() if keyword else ""
    )

    companies = [
        SearchCompanyHubspot(
            hubspot_company_id=company.id,
            company_name=company.properties.get("name"),
            domain=company.properties.get("domain"),
        )
        for company in companies.results
    ]

    return SearchCompanyHubspotResponse(
        total=len(companies),
        data=companies,
    )
