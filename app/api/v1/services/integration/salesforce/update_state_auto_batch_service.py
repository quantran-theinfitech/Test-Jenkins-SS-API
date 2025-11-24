from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.integration.salesforce import SalesforceStateAutoBatchRequest
from app.api.v1.schemas.users import UserBase
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)


def update_state_auto_batch(
    db: Session, current_user: UserBase, request: SalesforceStateAutoBatchRequest
):
    salesforce_integration = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == current_user.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    if salesforce_integration:
        salesforce_integration.auto_pull_companies = request.auto_pull_companies
        salesforce_integration.auto_pull_persons = request.auto_pull_persons
        salesforce_integration.auto_sync_companies = request.auto_sync_companies

        db.add(salesforce_integration)
        db.commit()
        db.refresh(salesforce_integration)
    else:
        raise NotFoundException(detail="integration.hubspot.notFoundConnection")
