from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.hubspot_connections import SaleSmartCompanySchemaResponse
from app.api.v1.schemas.users import UserBase
from app.constant.constants import MOCK_LIST_SCHEMA_SALE_SMART
from app.models import HubspotIntergrations


def listing_schema_sale_smart(
    db: Session, current_user: UserBase
) -> SaleSmartCompanySchemaResponse:
    hubspot_connection = db.exec(
        select(HubspotIntergrations).where(
            HubspotIntergrations.team_id == current_user.team_id,
            HubspotIntergrations.deleted_at.is_(None),
        )
    ).first()
    if not hubspot_connection:
        raise NotFoundException(detail="integration.hubspot.notFoundConnection")

    return SaleSmartCompanySchemaResponse(
        connection_id=hubspot_connection.id, data=MOCK_LIST_SCHEMA_SALE_SMART
    )
