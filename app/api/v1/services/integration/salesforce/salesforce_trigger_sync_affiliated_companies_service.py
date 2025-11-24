import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException, TooManyRequestsException
from app.api.v1.schemas.users import UserBase
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from app.models.integration.salesforce.salesforce_sync_histories import (
    TYPE_INTEGRATION_ENUM,
    SalesforceSyncHistories,
)
from batch.aws_batch import AWSBatchService, BatchManualAction


def salesforce_trigger_sync_affiliated_companies(
    db: Session,
    current_user: UserBase,
):
    salesforce_connection = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == current_user.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    if not salesforce_connection:
        raise NotFoundException(detail="common.notFound")

    salesforce_sync_detail = db.exec(
        select(SalesforceSyncHistories).where(
            SalesforceSyncHistories.salesforce_team_id
            == salesforce_connection.salesforce_team_id,
            SalesforceSyncHistories.salesforce_integration_id
            == salesforce_connection.id,
            SalesforceSyncHistories.type == TYPE_INTEGRATION_ENUM.SYNC_COMPANIES,
            SalesforceSyncHistories.status == 0,
            SalesforceSyncHistories.team_id == current_user.team_id,
        )
    ).first()

    if salesforce_sync_detail:
        now = datetime.now()
        if salesforce_sync_detail.created_at and (
            now - salesforce_sync_detail.created_at
        ) >= timedelta(days=1):
            salesforce_sync_detail.status = 2
            db.add(salesforce_sync_detail)
        else:
            raise TooManyRequestsException(
                detail="integration.salesforce.hasPullingCompanies"
            )

    try:
        salesforce_company_sync = SalesforceSyncHistories(
            salesforce_team_id=salesforce_connection.salesforce_team_id,
            salesforce_integration_id=salesforce_connection.id,
            team_id=current_user.team_id,
            type=TYPE_INTEGRATION_ENUM.SYNC_COMPANIES,
            status=0,
            method="MANUAL",
            log_id=str(uuid.uuid4()),
        )
        db.add(salesforce_company_sync)
        db.flush()
        db.commit()

        batch = AWSBatchService()
        batch.submit_job_by_log_id(
            BatchManualAction.SALESFORCE_SYNC_COMPANIES, salesforce_company_sync.log_id
        )

    except HTTPException as e:
        db.rollback()
        raise e
