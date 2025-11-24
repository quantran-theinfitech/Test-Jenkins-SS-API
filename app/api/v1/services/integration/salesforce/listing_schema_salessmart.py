from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.hubspot_connections import (
    SaleSmartCompanySchemaResponse,
    SaleSmartSchema,
)
from app.api.v1.schemas.users import UserBase
from app.constant.constants import MOCK_LIST_SCHEMA_SALE_SMART_SALESFORCE
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)


def listing_salesmart_company_schema(
    db: Session,
    current_user: UserBase,
) -> SaleSmartCompanySchemaResponse:
    salesforce_connection = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == current_user.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    if not salesforce_connection:
        raise NotFoundException(detail="integration.salesforce.notFoundConnection")

    return SaleSmartCompanySchemaResponse(
        connection_id=salesforce_connection.id,
        data=[
            SaleSmartSchema(**item) for item in MOCK_LIST_SCHEMA_SALE_SMART_SALESFORCE
        ],
    )
