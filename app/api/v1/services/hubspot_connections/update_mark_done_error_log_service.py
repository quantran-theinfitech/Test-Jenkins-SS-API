from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select, update

from app.api.base.exceptions import ConflictException, NotFoundException
from app.api.v1.schemas.hubspot_connections import (
    MarkDoneErrorLogHubspotRequest,
    TypeSync,
)
from app.models.integration.hubspot.hubspot_company_pull_histories import (
    HubspotCompanyPullHistories,
)
from app.models.integration.hubspot.hubspot_company_sync_histories import (
    HubspotCompanySyncHistories,
)
from app.models.integration.hubspot.hubspot_integrations import HubspotIntergrations
from app.models.integration.hubspot.hubspot_pull_person_histories import (
    HubspotPullPersonHistories,
)
from app.models.integration.hubspot.hubspot_raw_companies import HubspotRawCompanies
from app.models.integration.hubspot.hubspot_raw_persons import HubspotRawPersons


def update_mark_done_error_log(
    db: Session,
    team_id: int,
    request: MarkDoneErrorLogHubspotRequest,
):
    try:
        hubspot_connection = db.exec(
            select(HubspotIntergrations).where(
                HubspotIntergrations.team_id == team_id,
                HubspotIntergrations.deleted_at.is_(None),
            )
        ).first()

        if not hubspot_connection:
            raise NotFoundException(detail="integration.hubspot.notFoundConnection")

        if request.type_match == TypeSync.PULL_FROM_HUBSPOT:
            if request.hubspot_company_id is None:
                raise ConflictException(detail="common.hubspotCompanyIsNone")

            update_companies = (
                update(HubspotCompanyPullHistories)
                .where(
                    HubspotCompanyPullHistories.hubspot_company_id
                    == request.hubspot_company_id,
                    HubspotCompanyPullHistories.log_id
                    == HubspotCompanySyncHistories.log_id,
                    HubspotCompanySyncHistories.integration_id == hubspot_connection.id,
                    HubspotCompanySyncHistories.hubspot_team_id
                    == hubspot_connection.hubspot_team_id,
                    HubspotCompanySyncHistories.deleted_at.is_(None),
                    HubspotCompanyPullHistories.error_type.isnot(None),
                )
                .values(deleted_at=datetime.now())
                .execution_options(synchronize_session=False)
            )
            db.execute(update_companies)
            db.flush()

            update_raw_companies = (
                update(HubspotRawCompanies)
                .where(
                    HubspotRawCompanies.hubspot_company_id
                    == request.hubspot_company_id,
                    HubspotRawCompanies.integration_id == hubspot_connection.id,
                    HubspotRawCompanies.hubspot_team_id
                    == hubspot_connection.hubspot_team_id,
                )
                .values(deleted_at=datetime.now())
                .execution_options(synchronize_session=False)
            )

            db.execute(update_raw_companies)
            db.flush()

        if request.type_match == TypeSync.IDENTIFY_PERSON:
            if request.hubspot_person_id is None:
                raise ConflictException(detail="common.hubspotPersonIsNone")

            update_persons = (
                update(HubspotPullPersonHistories)
                .where(
                    HubspotPullPersonHistories.hubspot_person_id
                    == request.hubspot_person_id,
                    HubspotPullPersonHistories.log_id
                    == HubspotCompanySyncHistories.log_id,
                    HubspotCompanySyncHistories.integration_id == hubspot_connection.id,
                    HubspotCompanySyncHistories.hubspot_team_id
                    == hubspot_connection.hubspot_team_id,
                    HubspotCompanySyncHistories.deleted_at.is_(None),
                    HubspotPullPersonHistories.error_type.isnot(None),
                )
                .values(deleted_at=datetime.now())
                .execution_options(synchronize_session=False)
            )
            db.execute(update_persons)
            db.flush()

            update_raw_persons = (
                update(HubspotRawPersons)
                .where(
                    HubspotRawPersons.hubspot_person_id == request.hubspot_person_id,
                    HubspotRawPersons.integration_id == hubspot_connection.id,
                    HubspotRawPersons.hubspot_team_id
                    == hubspot_connection.hubspot_team_id,
                )
                .values(deleted_at=datetime.now())
                .execution_options(synchronize_session=False)
            )

            db.execute(update_raw_persons)
            db.flush()

        db.commit()
    except HTTPException as e:
        db.rollback()
        raise e
