from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.users import UserBase
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from app.models.integration.salesforce.salesforce_synced_companies import (
    SalesforceSyncedCompanies,
)


def delete_synced_company(db: Session, current_user: UserBase, corporate_number: str):
    salesforce_connection = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == current_user.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    if not salesforce_connection:
        raise NotFoundException(detail="common.notFound")

    salesforce_synced_company = db.exec(
        select(SalesforceSyncedCompanies).where(
            SalesforceSyncedCompanies.ss_company_id == corporate_number,
            SalesforceSyncedCompanies.deleted_at.is_(None),
            SalesforceSyncedCompanies.salesforce_integration_id
            == salesforce_connection.id,
            SalesforceSyncedCompanies.salesforce_team_id
            == salesforce_connection.salesforce_team_id,
        )
    ).first()

    if not salesforce_synced_company:
        raise NotFoundException(detail="company.notFound")

    try:
        db.delete(salesforce_synced_company)
        db.commit()
    except HTTPException as e:
        db.rollback()
        raise e
