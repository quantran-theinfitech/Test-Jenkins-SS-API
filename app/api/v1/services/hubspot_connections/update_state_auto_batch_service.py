from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.hubspot_connections import HubspotStateAutoBatchRequest
from app.api.v1.schemas.users import UserBase
from app.models.integration.hubspot.hubspot_integrations import HubspotIntergrations


def update_state_auto_batch(
    db: Session, current_user: UserBase, request: HubspotStateAutoBatchRequest
):
    hubspot_integration = db.exec(
        select(HubspotIntergrations).where(
            HubspotIntergrations.team_id == current_user.team_id,
            HubspotIntergrations.deleted_at.is_(None),
        )
    ).first()

    if hubspot_integration:
        hubspot_integration.auto_pull_companies = request.auto_pull_companies
        hubspot_integration.auto_pull_persons = request.auto_pull_persons
        hubspot_integration.auto_sync_companies = request.auto_sync_companies

        db.add(hubspot_integration)
        db.commit()
        db.refresh(hubspot_integration)
    else:
        raise NotFoundException(detail="integration.hubspot.notFoundConnection")
