from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.integration.salesforce import SalesforceCreateCustomFieldRequest
from app.api.v1.schemas.users import UserBase
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from utils.integration.salesforce import SalesforceService


def create_suggest_field_salesforce(
    db: Session,
    current_user: UserBase,
    request: SalesforceCreateCustomFieldRequest,
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

        salesforce_client = SalesforceService(
            access_token=salesforce_connection.access_token,
            refresh_token=salesforce_connection.refresh_token,
            instance_url=salesforce_connection.instance_url,
            id_url=salesforce_connection.id_url,
        )

        if request and len(request.custom_field) > 0:
            for field in request.custom_field:
                salesforce_client.create_custom_field(
                    name=field.name if field.name is not None else "",
                    label=field.label if field.label is not None else "",
                    type="Text",
                    length=255,
                )
    except HTTPException as e:
        raise e
