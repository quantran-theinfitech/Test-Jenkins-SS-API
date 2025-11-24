from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.integration.salesforce import SalesforceStateAutoBatchResponse
from app.api.v1.schemas.users import UserBase
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from app.models.integration.salesforce.salesforce_sync_histories import (
    SalesforceSyncHistories,
)


def get_state_auto_batch(db: Session, current_user: UserBase):
    salesforce_integration = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == current_user.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    last_time_pull_companies = None
    last_time_pull_persons = None
    last_time_sync_companies = None

    if salesforce_integration:
        last_pull_companies = db.exec(
            select(SalesforceSyncHistories)
            .where(
                SalesforceSyncHistories.salesforce_integration_id
                == salesforce_integration.id,
                SalesforceSyncHistories.deleted_at.is_(None),
                SalesforceSyncHistories.type == "PULL_COMPANIES",
            )
            .order_by(SalesforceSyncHistories.created_at.desc())
        ).first()

        last_pull_persons = db.exec(
            select(SalesforceSyncHistories)
            .where(
                SalesforceSyncHistories.salesforce_integration_id
                == salesforce_integration.id,
                SalesforceSyncHistories.deleted_at.is_(None),
                SalesforceSyncHistories.type == "PULL_PERSONS",
            )
            .order_by(SalesforceSyncHistories.created_at.desc())
        ).first()

        last_sync_companies = db.exec(
            select(SalesforceSyncHistories)
            .where(
                SalesforceSyncHistories.salesforce_integration_id
                == salesforce_integration.id,
                SalesforceSyncHistories.deleted_at.is_(None),
                SalesforceSyncHistories.type == "SYNC_COMPANIES",
            )
            .order_by(SalesforceSyncHistories.created_at.desc())
        ).first()

        last_time_pull_companies = (
            last_pull_companies.created_at if last_pull_companies else None
        )
        last_time_pull_persons = (
            last_pull_persons.created_at if last_pull_persons else None
        )
        last_time_sync_companies = (
            last_sync_companies.created_at if last_sync_companies else None
        )
    else:
        raise NotFoundException(detail="integration.salesforce.notFoundConnection")

    return SalesforceStateAutoBatchResponse(
        auto_pull_companies=salesforce_integration.auto_pull_companies,
        auto_pull_persons=salesforce_integration.auto_pull_persons,
        auto_sync_companies=salesforce_integration.auto_sync_companies,
        last_time_pull_companies=last_time_pull_companies,
        last_time_pull_persons=last_time_pull_persons,
        last_time_sync_companies=last_time_sync_companies,
    )
