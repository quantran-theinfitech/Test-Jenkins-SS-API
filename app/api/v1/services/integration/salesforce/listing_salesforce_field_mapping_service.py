from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import BadRequestException, NotFoundException
from app.api.v1.schemas.integration.salesforce import (
    SalesforceFieldMapping,
    SalesforceListingFieldMappingResponse,
)
from app.api.v1.schemas.users import UserBase
from app.models.integration.salesforce.salesforce_company_field_mappings import (
    SalesforceCompanyFieldMappings,
)
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)


def listing_salesforce_field_mappings(
    db: Session, current_user: UserBase
) -> SalesforceListingFieldMappingResponse:
    try:
        salesforce_connection = db.exec(
            select(SalesforceIntegrations).where(
                SalesforceIntegrations.team_id == current_user.team_id,
                SalesforceIntegrations.deleted_at.is_(None),
            )
        ).first()

        if not salesforce_connection:
            raise NotFoundException(detail="integration.salesforce.notFoundConnection")

        mappings = db.exec(
            select(SalesforceCompanyFieldMappings).where(
                SalesforceCompanyFieldMappings.salesforce_integration_id
                == salesforce_connection.id,
                SalesforceCompanyFieldMappings.salesforce_team_id
                == salesforce_connection.salesforce_team_id,
                SalesforceCompanyFieldMappings.team_id == current_user.team_id,
                SalesforceCompanyFieldMappings.deleted_at.is_(None),
            )
        ).all()

        return SalesforceListingFieldMappingResponse(
            connection_id=salesforce_connection.id,
            mapping_field=[
                SalesforceFieldMapping(
                    sale_smart_field=mapping.field,
                    salesforce_field=mapping.salesforce_field,
                    is_over_write=mapping.overwrite_flag,
                    is_auto_fill=mapping.autofill_flag,
                    field_class=mapping.field_class,
                )
                for mapping in mappings
            ],
        )
    except HTTPException as e:
        print("_______ error listing_salesforce_field_mappings _______", e)
        raise BadRequestException(
            detail="integration.salesforce.listingFieldMappingFailed"
        )
