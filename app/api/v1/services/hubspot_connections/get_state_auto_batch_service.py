from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.hubspot_connections import HubspotStateAutoBatchResponse
from app.api.v1.schemas.users import UserBase
from app.models.integration.hubspot.hubspot_company_sync_histories import (
    HubspotCompanySyncHistories,
)
from app.models.integration.hubspot.hubspot_integrations import HubspotIntergrations


def get_state_auto_batch(db: Session, current_user: UserBase):
    hubspot_integration = db.exec(
        select(HubspotIntergrations).where(
            HubspotIntergrations.team_id == current_user.team_id,
            HubspotIntergrations.deleted_at.is_(None),
        )
    ).first()

    last_time_pull_companies = None
    last_time_pull_persons = None
    last_time_sync_companies = None

    if hubspot_integration:
        last_time_pull_companies = db.exec(
            select(HubspotCompanySyncHistories)
            .where(
                HubspotCompanySyncHistories.integration_id == hubspot_integration.id,
                HubspotCompanySyncHistories.deleted_at.is_(None),
                HubspotCompanySyncHistories.type == "PULL",
            )
            .order_by(HubspotCompanySyncHistories.created_at.desc())
        ).first()

        last_time_pull_persons = db.exec(
            select(HubspotCompanySyncHistories)
            .where(
                HubspotCompanySyncHistories.integration_id == hubspot_integration.id,
                HubspotCompanySyncHistories.deleted_at.is_(None),
                HubspotCompanySyncHistories.type == "PERSON",
            )
            .order_by(HubspotCompanySyncHistories.created_at.desc())
        ).first()

        last_time_sync_companies = db.exec(
            select(HubspotCompanySyncHistories)
            .where(
                HubspotCompanySyncHistories.integration_id == hubspot_integration.id,
                HubspotCompanySyncHistories.deleted_at.is_(None),
                HubspotCompanySyncHistories.type == "SYNC",
            )
            .order_by(HubspotCompanySyncHistories.created_at.desc())
        ).first()

        last_time_pull_companies = (
            last_time_pull_companies.created_at if last_time_pull_companies else None
        )
        last_time_pull_persons = (
            last_time_pull_persons.created_at if last_time_pull_persons else None
        )
        last_time_sync_companies = (
            last_time_sync_companies.created_at if last_time_sync_companies else None
        )
    else:
        raise NotFoundException(detail="integration.hubspot.notFoundConnection")

    return HubspotStateAutoBatchResponse(
        auto_pull_companies=hubspot_integration.auto_pull_companies,
        auto_pull_persons=hubspot_integration.auto_pull_persons,
        auto_sync_companies=hubspot_integration.auto_sync_companies,
        last_time_pull_companies=last_time_pull_companies,
        last_time_pull_persons=last_time_pull_persons,
        last_time_sync_companies=last_time_sync_companies,
    )
