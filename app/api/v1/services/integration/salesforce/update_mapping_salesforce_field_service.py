from sqlmodel import Session, delete, select

from app.api.base.exceptions import BadRequestException, NotFoundException
from app.api.v1.schemas.integration.salesforce import (
    SalesforceUpdateMappingFieldRequest,
)
from app.api.v1.schemas.users import UserBase
from app.models.integration.salesforce.salesforce_company_field_mappings import (
    SalesforceCompanyFieldMappings,
)
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)


def update_mapping_salesforce_field(
    db: Session, current_user: UserBase, request: SalesforceUpdateMappingFieldRequest
):
    try:
        salesforce_connection = db.exec(
            select(SalesforceIntegrations).where(
                SalesforceIntegrations.team_id == current_user.team_id,
                SalesforceIntegrations.deleted_at.is_(None),
            )
        ).first()

        if not salesforce_connection:
            raise NotFoundException(detail="common.notFound")

        db.exec(
            delete(SalesforceCompanyFieldMappings).where(
                SalesforceCompanyFieldMappings.salesforce_integration_id
                == salesforce_connection.id,
                SalesforceCompanyFieldMappings.salesforce_team_id
                == salesforce_connection.salesforce_team_id,
            )
        )

        if request.data and len(request.data) > 0:
            for field in request.data:
                new_mapping = SalesforceCompanyFieldMappings(
                    salesforce_integration_id=salesforce_connection.id,
                    salesforce_team_id=salesforce_connection.salesforce_team_id,
                    salesforce_field=field.salesforce_field,
                    field=field.sale_smart_field,
                    overwrite_flag=field.is_over_write,
                    autofill_flag=field.is_auto_fill,
                    team_id=current_user.team_id,
                )
                db.add(new_mapping)

        db.commit()
        return True
    except Exception:
        db.rollback()
        raise BadRequestException(detail="integration.salesforce.updateMappingFailed")
