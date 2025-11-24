from typing import Optional

from sqlmodel import Session, func, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.integration.salesforce import (
    ListingSalesforceSyncLogsResponse,
    SalesforceSyncLogItem,
)
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
from app.models.integration.salesforce.salesforce_person_pull_histories import (
    SalesforcePersonPullHistories,
)
from app.models.integration.salesforce.salesforce_sync_histories import (
    SalesforceSyncHistories,
)


def listing_salesforce_sync_logs(
    db: Session,
    current_user: UserBase,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
) -> ListingSalesforceSyncLogsResponse:
    salesforce_connection = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == current_user.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    if not salesforce_connection:
        raise NotFoundException(detail="integration.salesforce.notFoundConnection")

    query = (
        select(SalesforceSyncHistories)
        .where(
            SalesforceSyncHistories.salesforce_team_id
            == salesforce_connection.salesforce_team_id,
            SalesforceSyncHistories.salesforce_integration_id
            == salesforce_connection.id,
            SalesforceSyncHistories.team_id == current_user.team_id,
            SalesforceSyncHistories.deleted_at.is_(None),
            SalesforceSyncHistories.type != "PULL_PERSONS",
        )
        .order_by(SalesforceSyncHistories.created_at.desc())
    )

    if page is not None and per_page is not None:
        query = query.offset((page - 1) * per_page)
        query = query.limit(per_page)

    listing_salesforce_sync_logs = db.exec(query).all()

    total = db.exec(
        select(func.count())
        .select_from(SalesforceSyncHistories)
        .where(
            SalesforceSyncHistories.salesforce_team_id
            == salesforce_connection.salesforce_team_id,
            SalesforceSyncHistories.salesforce_integration_id
            == salesforce_connection.id,
            SalesforceSyncHistories.team_id == current_user.team_id,
            SalesforceSyncHistories.deleted_at.is_(None),
            SalesforceSyncHistories.type != "PULL_PERSONS",
        )
    ).one()

    data = []
    if len(listing_salesforce_sync_logs) > 0:
        for sync_log in listing_salesforce_sync_logs:
            match_error_count = 0
            if sync_log.type == "PULL_COMPANIES":
                match_error_count = db.exec(
                    select(func.count())
                    .select_from(SalesforceCompanyPullHistories)
                    .where(
                        SalesforceCompanyPullHistories.log_id == sync_log.log_id,
                        SalesforceCompanyPullHistories.error_type.isnot(None),
                    )
                ).one()

            if sync_log.type == "PUSH_COMPANIES":
                match_error_count = db.exec(
                    select(func.count())
                    .select_from(SalesforceCompanyPushHistories)
                    .where(
                        SalesforceCompanyPushHistories.log_id == sync_log.log_id,
                        SalesforceCompanyPushHistories.error_type.isnot(None),
                    )
                ).one()

            if sync_log.type == "PULL_PERSONS":
                match_error_count = db.exec(
                    select(func.count())
                    .select_from(SalesforcePersonPullHistories)
                    .where(
                        SalesforcePersonPullHistories.log_id == sync_log.log_id,
                        SalesforcePersonPullHistories.error_type.isnot(None),
                    )
                ).one()

            data.append(
                SalesforceSyncLogItem(
                    id=sync_log.id if sync_log.id is not None else 0,
                    status=sync_log.status,
                    created_at=sync_log.created_at,
                    type_log=sync_log.type,
                    error_message=sync_log.error_message,
                    total_companies=sync_log.total_companies,
                    sync_count=sync_log.sync_count if sync_log.sync_count is not None else 0,
                    match_error_count=match_error_count,
                    match_success_count=sync_log.total_companies - match_error_count
                    if sync_log.total_companies
                    else 0,
                )
            )

    return ListingSalesforceSyncLogsResponse(
        data=data, total=total, page=page, per_page=per_page
    )
