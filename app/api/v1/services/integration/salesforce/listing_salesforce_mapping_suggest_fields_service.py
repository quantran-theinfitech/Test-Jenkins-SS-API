from sqlmodel import Session, select

from app.api.v1.schemas.integration.salesforce import (
    SalesforceFieldMapping,
    SalesforceListingFieldMappingResponse,
)
from app.api.v1.schemas.users import UserBase
from app.models.integration.salesforce.salesforce_field_mappings_default import (
    SalesforceFieldMappingDefault,
)


def listing_salesforce_mapping_suggest_fields(
    db: Session, current_user: UserBase
) -> SalesforceListingFieldMappingResponse:

    suggest_field_mappings = db.exec(
        select(SalesforceFieldMappingDefault).where(
            SalesforceFieldMappingDefault.is_suggested_field.is_(True),
            SalesforceFieldMappingDefault.deleted_at.is_(None),
        )
    ).all()

    return SalesforceListingFieldMappingResponse(
        mapping_field=[
            SalesforceFieldMapping(
                sale_smart_field=field.salesmart_field,
                salesforce_field=field.salesforce_field,
                is_over_write=field.is_over_write,
                is_auto_fill=field.is_auto_fill,
                field_class=field.field_class,
            )
            for field in suggest_field_mappings
            if field.salesforce_field and field.salesmart_field
        ],
    )
