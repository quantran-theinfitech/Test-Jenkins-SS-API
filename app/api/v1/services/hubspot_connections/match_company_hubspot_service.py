from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

import app.api.v1.services.companies as company_service
from app.api.base.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.api.v1.schemas.hubspot_connections import MatchCompanyHubspotRequest, TypeSync
from app.api.v1.schemas.users import UserBase
from app.models import HubspotIntergrations, HubspotSyncedCompanies
from app.models.integration.hubspot.hubspot_company_pull_histories import (
    HubspotCompanyPullHistories,
)
from app.models.integration.hubspot.hubspot_company_push_histories import (
    HubspotCompanyPushHistories,
)
from app.models.integration.hubspot.hubspot_pull_person_histories import (
    HubspotPullPersonHistories,
)
from batch.sync_company_data_to_hubspot import sync_company_data_to_husbpot


def match_company_hubspot(
    db: Session,
    current_user: UserBase,
    request: MatchCompanyHubspotRequest,
    manual_log_id: int,
    es_client,
):
    try:
        hubspot_connection = db.exec(
            select(HubspotIntergrations).where(
                HubspotIntergrations.team_id == current_user.team_id,
                HubspotIntergrations.deleted_at.is_(None),
            )
        ).first()

        hubspot_synced_companies_detail = None

        if request.type_match == TypeSync.PUSH_TO_HUBSPOT:
            hubspot_synced_companies_detail = db.exec(
                select(HubspotSyncedCompanies).where(
                    HubspotSyncedCompanies.hubspot_company_id
                    == request.hubspot_company_id,
                    HubspotSyncedCompanies.deleted_at.is_(None),
                    HubspotSyncedCompanies.integration_id == hubspot_connection.id,
                )
            ).first()
        elif (
            request.type_match == TypeSync.PULL_FROM_HUBSPOT
            or request.type_match == TypeSync.IDENTIFY_PERSON
        ):
            hubspot_synced_companies_detail = db.exec(
                select(HubspotSyncedCompanies).where(
                    HubspotSyncedCompanies.ss_company_id == request.ss_corporate_number,
                    HubspotSyncedCompanies.deleted_at.is_(None),
                    HubspotSyncedCompanies.integration_id == hubspot_connection.id,
                )
            ).first()

        if not hubspot_connection:
            raise NotFoundException(detail="integration.hubspot.notFoundConnection")

        if request.downloaded_flag is False and request.ss_corporate_number:
            company_service.download_companies(
                db, es_client, current_user, [request.ss_corporate_number]
            )

        if request.ss_corporate_number is None:
            raise ConflictException(detail="common.ssCompanyIsNone")

        if request.hubspot_company_id is None:
            raise ConflictException(detail="integration.hubspot.hubspotCompanyIsNone")

        if hubspot_synced_companies_detail is not None:
            raise BadRequestException(detail="integration.hubspot.companyIsLinked")

        company_synced = HubspotSyncedCompanies(
            ss_company_id=request.ss_corporate_number,
            integration_id=hubspot_connection.id,
            hubspot_team_id=hubspot_connection.hubspot_team_id,
            hubspot_company_id=request.hubspot_company_id,
            ss_company_fields=None,
        )
        db.add(company_synced)
        db.flush()
        db.refresh(company_synced)

        if request.type_match == TypeSync.PUSH_TO_HUBSPOT:
            history = db.exec(
                select(HubspotCompanyPushHistories).where(
                    HubspotCompanyPushHistories.id == manual_log_id
                )
            ).first()
            sync_company_data_to_husbpot(
                db=db,
                log_id=history.log_id,
                ss_company_id=request.ss_corporate_number,
                hubspot_company_id=request.hubspot_company_id,
            )
        elif request.type_match == TypeSync.PULL_FROM_HUBSPOT:
            history = db.exec(
                select(HubspotCompanyPullHistories).where(
                    HubspotCompanyPullHistories.id == manual_log_id
                )
            ).first()
            sync_company_data_to_husbpot(
                db=db,
                log_id=history.log_id,
                ss_company_id=request.ss_corporate_number,
                hubspot_company_id=request.hubspot_company_id,
            )
        elif request.type_match == TypeSync.IDENTIFY_PERSON:
            history = db.exec(
                select(HubspotPullPersonHistories).where(
                    HubspotPullPersonHistories.id == manual_log_id
                )
            ).first()

        history.error_type = None
        history.deleted_at = datetime.now()
        db.add(history)
        db.flush()
        db.refresh(history)

        db.commit()
    except HTTPException as e:
        db.rollback()
        raise e

    return company_synced.id
