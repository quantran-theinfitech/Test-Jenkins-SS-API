from typing import Optional

from sqlalchemy import func
from sqlmodel import Session, col, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.hubspot_connections import (
    HubspotSyncLogs,
    ListingHubspotSyncLogs,
)
from app.api.v1.schemas.users import UserBase
from app.models import HubspotCompanySyncHistories, HubspotIntergrations
from app.models.integration.hubspot.hubspot_company_pull_histories import (
    HubspotCompanyPullHistories,
)
from app.models.integration.hubspot.hubspot_company_push_histories import (
    HubspotCompanyPushHistories,
)
from app.models.integration.hubspot.hubspot_pull_person_histories import (
    HubspotPullPersonHistories,
)


def listing_hubspot_sync_log(
    db: Session,
    current_user: UserBase,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
):
    hubspot_connection = db.exec(
        select(HubspotIntergrations).where(
            HubspotIntergrations.team_id == current_user.team_id,
            HubspotIntergrations.deleted_at.is_(None),
        )
    ).first()

    if not hubspot_connection:
        raise NotFoundException(detail="integration.hubspot.notFoundConnection")

    query = (
        select(HubspotCompanySyncHistories)
        .where(
            HubspotCompanySyncHistories.hubspot_team_id
            == hubspot_connection.hubspot_team_id,
            HubspotCompanySyncHistories.integration_id == hubspot_connection.id,
            HubspotCompanySyncHistories.team_id == current_user.team_id,
            HubspotCompanySyncHistories.type != "PERSON",
        )
        .order_by(col(HubspotCompanySyncHistories.created_at).desc())
    )

    if page is not None and per_page is not None:
        query = query.offset((page - 1) * per_page)
        query = query.limit(per_page)

    listing_hubspot_sync_logs = db.exec(query).all()

    total = db.exec(
        select(func.count())
        .select_from(HubspotCompanySyncHistories)
        .where(
            HubspotCompanySyncHistories.hubspot_team_id
            == hubspot_connection.hubspot_team_id,
            HubspotCompanySyncHistories.integration_id == hubspot_connection.id,
            HubspotCompanySyncHistories.team_id == current_user.team_id,
            HubspotCompanySyncHistories.type != "PERSON",
        )
    ).one()

    data = []
    for sync_log in listing_hubspot_sync_logs:
        match_error_count = 0
        if sync_log.type == "PULL":
            match_error_count = db.exec(
                select(func.count())
                .select_from(HubspotCompanyPullHistories)
                .where(
                    HubspotCompanyPullHistories.log_id == sync_log.log_id,
                    HubspotCompanyPullHistories.error_type.isnot(None),
                )
            ).one()
        if sync_log.type == "PUSH":
            match_error_count = db.exec(
                select(func.count())
                .select_from(HubspotCompanyPushHistories)
                .where(
                    HubspotCompanyPushHistories.log_id == sync_log.log_id,
                    HubspotCompanyPushHistories.error_type.isnot(None),
                )
            ).one()

        if sync_log.type == "PERSON":
            match_error_count = db.exec(
                select(func.count())
                .select_from(HubspotPullPersonHistories)
                .where(
                    HubspotPullPersonHistories.log_id == sync_log.log_id,
                    HubspotPullPersonHistories.error_type.isnot(None),
                )
            ).one()

        data.append(
            HubspotSyncLogs(
                id=sync_log.id,
                status=sync_log.status,
                type_log=sync_log.type,
                created_at=sync_log.created_at,
                total_companies=sync_log.total_companies,
                error_message=sync_log.error_message,
                match_error_count=match_error_count,
                match_success_count=sync_log.total_companies - match_error_count
                if sync_log.total_companies
                else 0,
                sync_count=sync_log.sync_count if sync_log.sync_count else 0,
            )
        )

    return ListingHubspotSyncLogs(
        per_page=per_page,
        page=page,
        total=total,
        data=data,
    )
