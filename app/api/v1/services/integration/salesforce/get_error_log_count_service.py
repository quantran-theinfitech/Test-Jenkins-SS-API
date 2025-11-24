from sqlmodel import Session, and_, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.integration.salesforce import SalesforceStaticErrorLogResponse
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

# from app.models.integration.salesforce.salesforce_person_pull_histories import (
#     SalesforcePersonPullHistories,
# )
from app.models.integration.salesforce.salesforce_sync_histories import (
    SalesforceSyncHistories,
)
from app.models.integration.salesforce.salesforce_synced_companies import (
    SalesforceSyncedCompanies,
)
from utils.integration.salesforce import SalesforceService


def get_error_log_count(
    db: Session, current_user: UserBase
) -> SalesforceStaticErrorLogResponse:
    total = 0

    sf_connection = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == current_user.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    if not sf_connection:
        raise NotFoundException(detail="common.notFound")

    salesforce_service = SalesforceService(
        access_token=sf_connection.access_token,
        refresh_token=sf_connection.refresh_token,
        instance_url=sf_connection.instance_url,
        id_url=sf_connection.id_url,
    )

    salesforce_service.refresh_client()

    total_push_history = (
        db.query(SalesforceCompanyPushHistories)
        .join(
            SalesforceSyncHistories,
            and_(
                SalesforceSyncHistories.log_id == SalesforceCompanyPushHistories.log_id,
                SalesforceSyncHistories.deleted_at.is_(None),
            ),
        )
        .outerjoin(
            SalesforceSyncedCompanies,
            and_(
                SalesforceSyncedCompanies.ss_company_id
                == SalesforceCompanyPushHistories.ss_company_id,
                SalesforceSyncedCompanies.salesforce_integration_id == sf_connection.id,
                SalesforceSyncedCompanies.deleted_at.is_(None),
            ),
        )
        .where(
            SalesforceSyncHistories.salesforce_integration_id == sf_connection.id,
            SalesforceSyncHistories.salesforce_team_id
            == sf_connection.salesforce_team_id,
            SalesforceCompanyPushHistories.team_id == current_user.team_id,
            SalesforceCompanyPushHistories.deleted_at.is_(None),
            SalesforceCompanyPushHistories.error_type.isnot(None),
            SalesforceSyncedCompanies.id.is_(None),
        )
        .distinct(SalesforceCompanyPushHistories.ss_company_id)
        .count()
    )

    if total_push_history:
        total += total_push_history

    total_pull_history = (
        db.query(SalesforceCompanyPullHistories)
        .join(
            SalesforceSyncHistories,
            and_(
                SalesforceSyncHistories.log_id == SalesforceCompanyPullHistories.log_id,
                SalesforceSyncHistories.deleted_at.is_(None),
            ),
        )
        .outerjoin(
            SalesforceSyncedCompanies,
            and_(
                SalesforceSyncedCompanies.salesforce_company_id
                == SalesforceCompanyPullHistories.salesforce_company_id,
                SalesforceSyncedCompanies.salesforce_integration_id == sf_connection.id,
                SalesforceSyncedCompanies.deleted_at.is_(None),
            ),
        )
        .where(
            SalesforceSyncHistories.salesforce_team_id
            == sf_connection.salesforce_team_id,
            SalesforceSyncHistories.salesforce_integration_id == sf_connection.id,
            SalesforceCompanyPullHistories.team_id == current_user.team_id,
            SalesforceCompanyPullHistories.deleted_at.is_(None),
            SalesforceSyncedCompanies.id.is_(None),
            SalesforceCompanyPullHistories.error_type.isnot(None),
        )
        .distinct(SalesforceCompanyPullHistories.salesforce_company_id)
        .count()
    )

    if total_pull_history:
        total += total_pull_history

    # total_person_push_history = (
    #     db.query(SalesforcePersonPullHistories)
    #     .join(
    #         SalesforceSyncHistories,
    #         and_(
    #             SalesforceSyncHistories.log_id
    #             == SalesforcePersonPullHistories.log_id,
    #             SalesforceSyncHistories.deleted_at.is_(None),
    #         ),
    #     )
    #     .where(
    #         SalesforceSyncHistories.salesforce_integration_id == sf_connection.id,
    #         SalesforceSyncHistories.salesforce_team_id
    #         == sf_connection.salesforce_team_id,
    #         SalesforceSyncHistories.team_id == current_user.team_id,
    #         SalesforcePersonPullHistories.deleted_at.is_(None),
    #         SalesforcePersonPullHistories.error_type.isnot(None),
    #     )
    #     .distinct(SalesforcePersonPullHistories.salesforce_person_id)
    #     .count()
    # )

    # if total_person_push_history:
    #     total += total_person_push_history

    return SalesforceStaticErrorLogResponse(
        total=total,
        total_pull_history=total_pull_history,
        total_push_history=total_push_history,
    )
