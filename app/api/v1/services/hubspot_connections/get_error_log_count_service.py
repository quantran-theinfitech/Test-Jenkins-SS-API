from sqlmodel import Session, and_, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.hubspot_connections import HubspotStaticErrorLogResponse
from app.api.v1.schemas.users import UserBase
from app.models.integration.hubspot.hubspot_company_pull_histories import (
    HubspotCompanyPullHistories,
)
from app.models.integration.hubspot.hubspot_company_push_histories import (
    HubspotCompanyPushHistories,
)
from app.models.integration.hubspot.hubspot_company_sync_histories import (
    HubspotCompanySyncHistories,
)
from app.models.integration.hubspot.hubspot_integrations import HubspotIntergrations

# from app.models.integration.hubspot.hubspot_pull_person_histories import (
#     HubspotPullPersonHistories,
# )
from app.models.integration.hubspot.hubspot_synced_companies import (
    HubspotSyncedCompanies,
)
from utils.hubspot_connection import HubSpotService


def get_error_log_count(
    db: Session, current_user: UserBase
) -> HubspotStaticErrorLogResponse:
    hubspot_connection = db.exec(
        select(HubspotIntergrations).where(
            HubspotIntergrations.team_id == current_user.team_id,
            HubspotIntergrations.deleted_at.is_(None),
        )
    ).first()

    if not hubspot_connection:
        raise NotFoundException(detail="common.notFound")

    hubspot_service = HubSpotService(
        access_token=hubspot_connection.access_token,
        refresh_token=hubspot_connection.refresh_token,
    )
    hubspot_service.refresh_client()

    total = 0

    total_push_history_query = (
        db.query(HubspotCompanyPushHistories)
        .join(
            HubspotCompanySyncHistories,
            and_(
                HubspotCompanySyncHistories.log_id
                == HubspotCompanyPushHistories.log_id,
                HubspotCompanySyncHistories.deleted_at.is_(None),
            ),
        )
        .outerjoin(
            HubspotSyncedCompanies,
            and_(
                HubspotSyncedCompanies.ss_company_id
                == HubspotCompanyPushHistories.ss_company_id,
                HubspotSyncedCompanies.integration_id == hubspot_connection.id,
                HubspotSyncedCompanies.deleted_at.is_(None),
            ),
        )
        .filter(
            HubspotCompanySyncHistories.integration_id == hubspot_connection.id,
            HubspotCompanySyncHistories.hubspot_team_id
            == hubspot_connection.hubspot_team_id,
            HubspotCompanyPushHistories.deleted_at.is_(None),
            HubspotCompanyPushHistories.error_type.isnot(None),
            HubspotSyncedCompanies.id.is_(None),
        )
        .distinct(HubspotCompanyPushHistories.ss_company_id)
    )

    total_push_history = total_push_history_query.count()

    if total_push_history:
        total += total_push_history

    total_pull_history_query = (
        db.query(HubspotCompanyPullHistories)
        .join(
            HubspotCompanySyncHistories,
            and_(
                HubspotCompanySyncHistories.log_id
                == HubspotCompanyPullHistories.log_id,
                HubspotCompanySyncHistories.deleted_at.is_(None),
            ),
        )
        .outerjoin(
            HubspotSyncedCompanies,
            and_(
                HubspotSyncedCompanies.hubspot_company_id
                == HubspotCompanyPullHistories.hubspot_company_id,
                HubspotSyncedCompanies.integration_id == hubspot_connection.id,
                HubspotSyncedCompanies.deleted_at.is_(None),
            ),
        )
        .filter(
            HubspotCompanySyncHistories.integration_id == hubspot_connection.id,
            HubspotCompanySyncHistories.hubspot_team_id
            == hubspot_connection.hubspot_team_id,
            HubspotCompanyPullHistories.deleted_at.is_(None),
            HubspotCompanyPullHistories.error_type.isnot(None),
            HubspotSyncedCompanies.id.is_(None),
        )
        .distinct(HubspotCompanyPullHistories.hubspot_company_id)
    )

    total_pull_history = total_pull_history_query.count()

    if total_pull_history:
        total += total_pull_history

    # total_pull_person_query = (
    #     db.query(HubspotPullPersonHistories)
    #     .join(
    #         HubspotCompanySyncHistories,
    #         and_(
    #             HubspotCompanySyncHistories.log_id
    #             == HubspotPullPersonHistories.log_id,
    #             HubspotCompanySyncHistories.deleted_at.is_(None),
    #         ),
    #     )
    #     .outerjoin(
    #         HubspotSyncedCompanies,
    #         and_(
    #             HubspotSyncedCompanies.hubspot_company_id
    #             == HubspotPullPersonHistories.hubspot_company_id,
    #             HubspotSyncedCompanies.integration_id == hubspot_connection.id,
    #             HubspotSyncedCompanies.deleted_at.is_(None),
    #         ),
    #     )
    #     .filter(
    #         HubspotCompanySyncHistories.integration_id == hubspot_connection.id,
    #         HubspotCompanySyncHistories.hubspot_team_id
    #         == hubspot_connection.hubspot_team_id,
    #         HubspotPullPersonHistories.deleted_at.is_(None),
    #         HubspotPullPersonHistories.error_type.isnot(None),
    #         HubspotSyncedCompanies.id.is_(None),
    #     )
    #     .distinct(HubspotPullPersonHistories.hubspot_person_id)
    # )

    # total_pull_person = total_pull_person_query.count()

    # if total_pull_person:
    #     total += total_pull_person

    return HubspotStaticErrorLogResponse(
        total=total,
        total_push_history=total_push_history,
        total_pull_history=total_pull_history,
    )
