from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.integration.salesforce import (
    SalesforceListingCompnaySchemaResponse,
)
from app.api.v1.schemas.users import UserBase
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from utils.integration.salesforce import SalesforceService


def listing_salesforce_company_schema(
    db: Session, current_user: UserBase
) -> SalesforceListingCompnaySchemaResponse:
    try:
        salesforce_connection = db.exec(
            select(SalesforceIntegrations).where(
                SalesforceIntegrations.team_id == current_user.team_id,
                SalesforceIntegrations.deleted_at.is_(None),
            )
        ).first()

        if not salesforce_connection:
            raise NotFoundException(detail="integration.salesforce.notFoundConnection")

        salesforce_service = SalesforceService(
            access_token=salesforce_connection.access_token,
            refresh_token=salesforce_connection.refresh_token,
            instance_url=salesforce_connection.instance_url,
            id_url=salesforce_connection.id_url,
        )

        schema = salesforce_service.get_company_schema()

        return SalesforceListingCompnaySchemaResponse(
            connection_id=salesforce_connection.id, data=schema
        )

    except HTTPException as e:
        raise e
