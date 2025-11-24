from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.v1.schemas.hubspot_connections import GetSyncedCompanyResponse
from app.api.v1.schemas.users import UserBase
from app.models import Company, HubspotIntergrations, HubspotSyncedCompanies
from utils.hubspot_connection import HubSpotService


def get_synced_company(
    db: Session, current_user: UserBase, corporate_number: str
) -> GetSyncedCompanyResponse:
    hubspot_connection = db.exec(
        select(HubspotIntergrations).where(
            HubspotIntergrations.team_id == current_user.team_id,
            HubspotIntergrations.deleted_at.is_(None),
        )
    ).first()

    if not hubspot_connection:
        return GetSyncedCompanyResponse(is_synced=False)

    hubspot_synced_company = db.exec(
        select(HubspotSyncedCompanies).where(
            HubspotSyncedCompanies.hubspot_team_id
            == hubspot_connection.hubspot_team_id,
            HubspotSyncedCompanies.integration_id == hubspot_connection.id,
            HubspotSyncedCompanies.deleted_at.is_(None),
            HubspotSyncedCompanies.ss_company_id == corporate_number,
        )
    ).first()
    if not hubspot_synced_company:
        return GetSyncedCompanyResponse(is_synced=False)

    ss_company = db.exec(
        select(Company).where(Company.corporate_number == corporate_number)
    ).first()

    try:
        hubspot_service = HubSpotService(
            access_token=hubspot_connection.access_token,
            refresh_token=hubspot_connection.refresh_token,
        )

        synced_company_info = hubspot_service.get_company_by_id(
            hubspot_synced_company.hubspot_company_id
        )
    except HTTPException as e:
        hubspot_synced_company.deleted_at = datetime.now()
        db.add(hubspot_synced_company)
        db.commit()
        raise e

    return GetSyncedCompanyResponse(
        is_synced=True,
        ss_company_name=ss_company.name,
        hubspot_team_id=hubspot_connection.hubspot_team_id,
        hubspot_company_id=hubspot_synced_company.hubspot_company_id,
        hubspot_company_name=synced_company_info.properties.get("name"),
    )
