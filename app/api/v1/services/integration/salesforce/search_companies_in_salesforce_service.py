from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.integration.salesforce import (
    ListingSalesforceCompaniesResponse,
    SalesforcePushErrorLogCompany,
)
from app.api.v1.schemas.users import UserBase
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from utils.integration.salesforce import SalesforceService


def search_companies_in_salesforce(
    current_user: UserBase,
    db: Session,
    keyword: Optional[str],
) -> ListingSalesforceCompaniesResponse:
    try:
        sf_connection = db.exec(
            select(SalesforceIntegrations).where(
                SalesforceIntegrations.team_id == current_user.team_id,
                SalesforceIntegrations.deleted_at.is_(None),
            )
        ).first()

        if not sf_connection:
            raise NotFoundException(detail="common.notFound")

        salesforce_service = SalesforceService(
            access_token=sf_connection.access_token,
            refresh_token=sf_connection.refresh_token,
            instance_url=sf_connection.instance_url,
            id_url=sf_connection.id_url,
        )

        data = []

        if keyword:
            salesforce_companies = salesforce_service.search_companies(
                search_string=keyword.lower()
            )

            if len(salesforce_companies) > 0:
                data = [
                    SalesforcePushErrorLogCompany(
                        salesforce_company_id=company.get("Id"),
                        salesforce_company_name=company.get("Name"),
                        domain=company.get("Website"),
                    )
                    for company in salesforce_companies
                ]

        return ListingSalesforceCompaniesResponse(
            total=len(data),
            data=data,
        )
    except HTTPException as e:
        raise e
