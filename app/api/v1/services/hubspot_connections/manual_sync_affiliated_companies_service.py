import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException, TooManyRequestsException
from app.api.v1.schemas.users import UserBase
from app.models import HubspotIntergrations
from app.models.integration.hubspot.hubspot_company_sync_histories import (
    HubspotCompanySyncHistories,
)
from batch.aws_batch import AWSBatchService, BatchManualAction


def manual_sync_affiliated_companies(db: Session, current_user: UserBase):
    hubspot_connection = db.exec(
        select(HubspotIntergrations).where(
            HubspotIntergrations.team_id == current_user.team_id,
            HubspotIntergrations.deleted_at.is_(None),
        )
    ).first()

    if not hubspot_connection:
        raise NotFoundException(detail="integration.hubspot.notFoundConnection")

    hubspot_company_sync_detail = db.exec(
        select(HubspotCompanySyncHistories).where(
            HubspotCompanySyncHistories.hubspot_team_id
            == hubspot_connection.hubspot_team_id,
            HubspotCompanySyncHistories.integration_id == hubspot_connection.id,
            HubspotCompanySyncHistories.type == "SYNC",
            HubspotCompanySyncHistories.status == 0,
            HubspotCompanySyncHistories.team_id == current_user.team_id,
        )
    ).first()

    if hubspot_company_sync_detail:
        now = datetime.now()
        if hubspot_company_sync_detail.created_at and (
            now - hubspot_company_sync_detail.created_at
        ) >= timedelta(days=1):
            hubspot_company_sync_detail.status = 2
            db.add(hubspot_company_sync_detail)
        else:
            raise TooManyRequestsException(
                detail="integration.hubspot.hasPullingCompanies"
            )

    try:
        hubspot_company_sync = HubspotCompanySyncHistories(
            hubspot_team_id=hubspot_connection.hubspot_team_id,
            integration_id=hubspot_connection.id,
            team_id=current_user.team_id,
            type="SYNC",
            status=0,
            hubspot_push_type="MANUAL",
            log_id=str(uuid.uuid4()),
        )
        db.add(hubspot_company_sync)
        db.flush()
        db.commit()

        batch = AWSBatchService()
        batch.submit_job_by_log_id(
            BatchManualAction.HUBSPOT_SYNC_COMPANIES, hubspot_company_sync.log_id
        )

    except HTTPException as e:
        db.rollback()
        raise e

    return hubspot_company_sync.id
