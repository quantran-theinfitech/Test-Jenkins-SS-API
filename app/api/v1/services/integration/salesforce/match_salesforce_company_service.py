from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

import app.api.v1.services.companies as company_service
from app.api.base.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.api.v1.schemas.hubspot_connections import TypeSync
from app.api.v1.schemas.integration.salesforce import SalesforceMatchCompanyRequest
from app.api.v1.schemas.users import UserBase
from app.models.integration.salesforce.salesforce_company_pull_histories import (
    SalesforceCompanyPullHistories,
)
from app.models.integration.salesforce.salesforce_company_push_histories import (
    SalesforceCompanyPushHistories,
)
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from app.models.integration.salesforce.salesforce_synced_companies import (
    SalesforceSyncedCompanies,
)
from batch.sync_company_data_to_salesforce import sync_company_data_to_salesforce


def match_salesforce_company(
    db: Session,
    current_user: UserBase,
    request: SalesforceMatchCompanyRequest,
    error_log_id: int,
    es_client,
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

        if request.downloaded_flag is False and request.ss_corporate_number:
            company_service.download_companies(
                db, es_client, current_user, [request.ss_corporate_number]
            )

        if request.ss_corporate_number is None:
            raise ConflictException(detail="common.ssCompanyIsNone")

        if request.salesforce_company_id is None:
            raise ConflictException(
                detail="integration.salesforce.salesforceCompanyIsNone"
            )

        salesforce_synced_company = None

        if request.type_match == TypeSync.PUSH_TO_HUBSPOT:
            salesforce_synced_company = db.exec(
                select(SalesforceSyncedCompanies).where(
                    SalesforceSyncedCompanies.salesforce_company_id
                    == request.salesforce_company_id,
                    SalesforceSyncedCompanies.deleted_at.is_(None),
                    SalesforceSyncedCompanies.salesforce_integration_id
                    == salesforce_connection.id,
                    SalesforceSyncedCompanies.salesforce_team_id
                    == salesforce_connection.salesforce_team_id,
                )
            ).first()
        elif request.type_match == TypeSync.PULL_FROM_HUBSPOT:
            salesforce_synced_company = db.exec(
                select(SalesforceSyncedCompanies).where(
                    SalesforceSyncedCompanies.ss_company_id
                    == request.ss_corporate_number,
                    SalesforceSyncedCompanies.deleted_at.is_(None),
                    SalesforceSyncedCompanies.salesforce_integration_id
                    == salesforce_connection.id,
                    SalesforceSyncedCompanies.salesforce_team_id
                    == salesforce_connection.salesforce_team_id,
                )
            ).first()

        if salesforce_synced_company is not None:
            raise BadRequestException(detail="integration.salesforce.companyIsLinked")

        company_synced = SalesforceSyncedCompanies(
            ss_company_id=request.ss_corporate_number,
            salesforce_integration_id=salesforce_connection.id,
            salesforce_team_id=salesforce_connection.salesforce_team_id,
            salesforce_company_id=request.salesforce_company_id,
        )
        db.add(company_synced)
        db.flush()
        db.refresh(company_synced)

        if request.type_match == TypeSync.PUSH_TO_HUBSPOT:
            history = db.exec(
                select(SalesforceCompanyPushHistories).where(
                    SalesforceCompanyPushHistories.id == error_log_id,
                    SalesforceCompanyPushHistories.team_id == current_user.team_id,
                    SalesforceCompanyPushHistories.salesforce_integration_id
                    == salesforce_connection.id,
                    SalesforceCompanyPushHistories.deleted_at.is_(None),
                )
            ).first()
            sync_company_data_to_salesforce(
                db=db,
                log_id=history.log_id,
                ss_company_id=request.ss_corporate_number,
                salesforce_company_id=request.salesforce_company_id,
            )
        elif request.type_match == TypeSync.PULL_FROM_HUBSPOT:
            history = db.exec(
                select(SalesforceCompanyPullHistories).where(
                    SalesforceCompanyPullHistories.id == error_log_id,
                    SalesforceCompanyPullHistories.team_id == current_user.team_id,
                    SalesforceCompanyPullHistories.salesforce_integration_id
                    == salesforce_connection.id,
                    SalesforceCompanyPullHistories.deleted_at.is_(None),
                )
            ).first()
            sync_company_data_to_salesforce(
                db=db,
                log_id=history.log_id,
                ss_company_id=request.ss_corporate_number,
                salesforce_company_id=request.salesforce_company_id,
            )

        history.deleted_at = datetime.now()
        db.add(history)
        db.flush()
        db.commit()
    except HTTPException as e:
        db.rollback()
        raise e
