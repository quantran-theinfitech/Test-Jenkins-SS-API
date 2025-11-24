from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select, update

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.hubspot_connections import TypeSync
from app.api.v1.schemas.integration.salesforce import SalesforceMarkDoneErrorLogRequest
from app.api.v1.schemas.users import UserBase
from app.models.integration.salesforce.salesforce_company_pull_histories import (
    SalesforceCompanyPullHistories,
)
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from app.models.integration.salesforce.salesforce_person_pull_histories import (
    SalesforcePersonPullHistories,
)
from app.models.integration.salesforce.salesforce_raw_companies import (
    SalesforceRawCompanies,
)
from app.models.integration.salesforce.salesforce_raw_persons import (
    SalesforceRawPersons,
)
from app.models.integration.salesforce.salesforce_sync_histories import (
    SalesforceSyncHistories,
)


def update_mark_done_error_log(
    db: Session, current_user: UserBase, request: SalesforceMarkDoneErrorLogRequest
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

        if request.type_match == TypeSync.PULL_FROM_HUBSPOT:
            if request.salesforce_company_id is None:
                raise NotFoundException(
                    detail="integration.salesforce.salesforceCompanyIsNone"
                )

            update_companies = (
                update(SalesforceCompanyPullHistories)
                .where(
                    SalesforceCompanyPullHistories.salesforce_company_id
                    == request.salesforce_company_id,
                    SalesforceCompanyPullHistories.log_id
                    == SalesforceSyncHistories.log_id,
                    SalesforceSyncHistories.salesforce_integration_id
                    == salesforce_connection.id,
                    SalesforceSyncHistories.salesforce_team_id
                    == salesforce_connection.salesforce_team_id,
                    SalesforceSyncHistories.deleted_at.is_(None),
                    SalesforceCompanyPullHistories.error_type.isnot(None),
                    SalesforceCompanyPullHistories.deleted_at.is_(None),
                )
                .values(deleted_at=datetime.now())
                .execution_options(synchronize_session=False)
            )

            db.execute(update_companies)
            db.commit()

            update_raw_companies = (
                update(SalesforceRawCompanies)
                .where(
                    SalesforceRawCompanies.salesforce_company_id
                    == request.salesforce_company_id,
                    SalesforceRawCompanies.salesforce_integration_id
                    == salesforce_connection.id,
                    SalesforceRawCompanies.salesforce_team_id
                    == salesforce_connection.salesforce_team_id,
                )
                .values(deleted_at=datetime.now())
                .execution_options(synchronize_session=False)
            )

            db.execute(update_raw_companies)
            db.flush()

        if request.type_match == TypeSync.IDENTIFY_PERSON:
            if request.salesforce_person_id is None:
                raise NotFoundException(
                    detail="integration.salesforce.salesforcePersonIsNone"
                )

            update_persons = (
                update(SalesforcePersonPullHistories)
                .where(
                    SalesforcePersonPullHistories.salesforce_person_id
                    == request.salesforce_person_id,
                    SalesforcePersonPullHistories.log_id
                    == SalesforceSyncHistories.log_id,
                    SalesforceSyncHistories.salesforce_integration_id
                    == salesforce_connection.id,
                    SalesforceSyncHistories.salesforce_team_id
                    == salesforce_connection.salesforce_team_id,
                    SalesforceSyncHistories.deleted_at.is_(None),
                    SalesforcePersonPullHistories.error_type.isnot(None),
                )
                .values(deleted_at=datetime.now())
                .execution_options(synchronize_session=False)
            )

            db.execute(update_persons)
            db.flush()

            update_raw_persons = (
                update(SalesforceRawPersons)
                .where(
                    SalesforceRawPersons.salesforce_person_id
                    == request.salesforce_person_id,
                    SalesforceRawPersons.salesforce_integration_id
                    == salesforce_connection.id,
                    SalesforceRawPersons.salesforce_team_id
                    == salesforce_connection.salesforce_team_id,
                )
                .values(deleted_at=datetime.now())
                .execution_options(synchronize_session=False)
            )

            db.execute(update_raw_persons)
            db.flush()

        db.commit()

    except HTTPException as e:
        print("_______ error update_mark_done_salesforce_error_log _______", str(e))
        db.rollback()
        raise e
