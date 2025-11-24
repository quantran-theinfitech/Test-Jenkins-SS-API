from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.v1.schemas.integration.salesforce import SalesforceSyncedCompanyResponse
from app.api.v1.schemas.users import UserBase
from app.models.company import Company
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from app.models.integration.salesforce.salesforce_synced_companies import (
    SalesforceSyncedCompanies,
)
from utils.integration.salesforce import SalesforceService


def get_synced_company(
    db: Session, current_user: UserBase, corporate_number: str
) -> SalesforceSyncedCompanyResponse:
    salesforce_connection = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == current_user.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    if not salesforce_connection:
        return SalesforceSyncedCompanyResponse(is_synced=False)

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
        return SalesforceSyncedCompanyResponse(is_synced=False)

    ss_company = db.exec(
        select(Company).where(Company.corporate_number == corporate_number)
    ).first()

    try:
        salesforce_service = SalesforceService(
            access_token=salesforce_connection.access_token,
            refresh_token=salesforce_connection.refresh_token,
            instance_url=salesforce_connection.instance_url,
            id_url=salesforce_connection.id_url,
        )

        synced_company_info = salesforce_service.get_company_by_id(
            salesforce_synced_company.salesforce_company_id
        )
    except HTTPException as e:
        salesforce_synced_company.deleted_at = datetime.now()
        db.add(salesforce_synced_company)
        db.commit()
        raise e

    return SalesforceSyncedCompanyResponse(
        is_synced=True,
        ss_company_name=ss_company.name,
        salesforce_team_id=salesforce_connection.salesforce_team_id,
        salesforce_company_id=salesforce_synced_company.salesforce_company_id,
        salesforce_company_name=synced_company_info.get("Name"),
        url=f"""
            {salesforce_connection.instance_url}/{salesforce_synced_company.salesforce_company_id}
        """
        if salesforce_connection.instance_url
        and salesforce_synced_company.salesforce_company_id
        else None,
    )
