from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.hubspot_connections import (
    HubspotMapping,
    HubspotMappingSettingResponse,
)
from app.api.v1.schemas.users import UserBase
from app.models import HubspotCompanyFieldMappings, HubspotIntergrations
from app.models.integration.hubspot.field_mapping_hubspot import FieldMappingHubspot


def listing_mapping(
    db: Session,
    current_user: UserBase,
) -> HubspotMappingSettingResponse:
    hubspot_connection = db.exec(
        select(HubspotIntergrations).where(
            HubspotIntergrations.team_id == current_user.team_id,
            HubspotIntergrations.deleted_at.is_(None),
        )
    ).first()
    if not hubspot_connection:
        raise NotFoundException(detail="integration.hubspot.notFoundConnection")

    field_mapping = db.exec(
        select(HubspotCompanyFieldMappings).where(
            HubspotCompanyFieldMappings.integration_id == hubspot_connection.id,
            HubspotCompanyFieldMappings.hubspot_team_id
            == hubspot_connection.hubspot_team_id,
        )
    ).all()

    return HubspotMappingSettingResponse(
        connection_id=hubspot_connection.id,
        mapping_field=[
            HubspotMapping(
                sale_smart_field=field.field,
                hubspot_field=field.hubspot_field,
                is_over_write=field.overwrite_flag,
                is_auto_fill=field.autofill_flag,
            )
            for field in field_mapping
        ],
    )


def listing_mapping_suggest_field(
    db: Session,
    current_user: UserBase,
) -> HubspotMappingSettingResponse:
    suggest_field_mappings = db.exec(
        select(FieldMappingHubspot).where(
            FieldMappingHubspot.is_suggested_field.is_(True)
        )
    ).all()

    return HubspotMappingSettingResponse(
        mapping_field=[
            HubspotMapping(
                sale_smart_field=field.sale_smart_field,
                hubspot_field=field.hubspot_field,
                is_over_write=field.is_over_write,
                is_auto_fill=field.is_auto_fill,
            )
            for field in suggest_field_mappings
            if field.hubspot_field and field.sale_smart_field
        ],
    )
