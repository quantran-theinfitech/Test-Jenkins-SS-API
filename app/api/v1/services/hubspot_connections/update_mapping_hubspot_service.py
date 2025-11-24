from fastapi import HTTPException
from sqlmodel import Session, delete, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.hubspot_connections import UpdateMappingFieldRequest
from app.api.v1.schemas.users import UserBase
from app.models import HubspotCompanyFieldMappings, HubspotIntergrations


def update_mapping_hubspot(
    db: Session, current_user: UserBase, req: UpdateMappingFieldRequest
):
    try:
        # Lấy thông tin tích hợp HubSpot
        hubspot_connection = db.exec(
            select(HubspotIntergrations).where(
                HubspotIntergrations.team_id == current_user.team_id,
                HubspotIntergrations.deleted_at.is_(None),
            )
        ).first()

        if not hubspot_connection:
            raise NotFoundException(detail="integration.hubspot.notFoundConnection")

        # Xóa các bản ghi cũ liên quan đến integration_id và hubspot_team_id
        db.exec(
            delete(HubspotCompanyFieldMappings).where(
                HubspotCompanyFieldMappings.integration_id == hubspot_connection.id,
                HubspotCompanyFieldMappings.hubspot_team_id
                == hubspot_connection.hubspot_team_id,
            )
        )

        for field in req.data:
            new_mapping = HubspotCompanyFieldMappings(
                integration_id=hubspot_connection.id,
                hubspot_team_id=hubspot_connection.hubspot_team_id,
                hubspot_field=field.hubspot_field,
                field=field.sale_smart_field,
                overwrite_flag=field.is_over_write,
                autofill_flag=field.is_auto_fill,
            )
            db.add(new_mapping)

        db.commit()
        return hubspot_connection.id
    except HTTPException as e:
        # Rollback nếu có lỗi xảy ra
        db.rollback()
        raise e
