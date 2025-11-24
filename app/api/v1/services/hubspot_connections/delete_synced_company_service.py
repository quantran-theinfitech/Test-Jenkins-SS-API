from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.users import UserBase
from app.models import HubspotIntergrations, HubspotSyncedCompanies


def delete_synced_company(
    db: Session, current_user: UserBase, corporate_number: str
) -> int:
    hubspot_connection = db.exec(
        select(HubspotIntergrations).where(
            HubspotIntergrations.team_id == current_user.team_id,
            HubspotIntergrations.deleted_at.is_(None),
        )
    ).first()

    if not hubspot_connection:
        raise NotFoundException(detail="integration.hubspot.notFoundConnection")

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
        raise NotFoundException(detail="integration.hubspot.notFoundCompanyInHubspot")

    try:
        db.delete(hubspot_synced_company)
        db.commit()
        return corporate_number

    except HTTPException as e:
        db.rollback()
        raise e
