from typing import Optional

from sqlmodel import Session, and_, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.integration.salesforce import (
    ListingSalesforcePushErrorLogsResponse,
    SalesforcePushErrorLogCompany,
    SalesforcePushErrorLogDetailResponse,
    SalesforcePushErrorLogItem,
)
from app.api.v1.schemas.users import UserBase
from app.models import (
    SalesforceCompanyMultiplePushHistories,
    SalesforceCompanyPushHistories,
    SalesforceIntegrations,
    SalesforceSyncedCompanies,
    SalesforceSyncHistories,
)
from app.models.company import Company
from app.models.team import PlanCode
from app.models.team_company import TeamCompany
from utils.integration.salesforce import SalesforceService


def listing_salesforce_push_error_logs(
    db: Session,
    listing_plan_code: PlanCode,
    current_user: UserBase,
    per_page: Optional[int] = None,
    page: Optional[int] = None,
) -> ListingSalesforcePushErrorLogsResponse:
    sf_connection = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == current_user.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    if not sf_connection:
        raise NotFoundException(detail="common.notFound")

    total = (
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

    query = (
        select(SalesforceCompanyPushHistories)
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
        .order_by(
            SalesforceCompanyPushHistories.ss_company_id,
            SalesforceCompanyPushHistories.created_at.desc(),
        )
    )

    if page is not None and per_page is not None:
        query = query.offset((page - 1) * per_page).limit(per_page)

    results = db.exec(query).all()
    data = []

    for result in results:
        ss_company = db.exec(
            select(Company).where(Company.corporate_number == result.ss_company_id)
        ).first()
        if listing_plan_code == PlanCode.UNLIMITED:
            data.append(
                SalesforcePushErrorLogItem(
                    id=result.id,
                    ss_corporate_number=result.ss_company_id,
                    ss_company_name=ss_company.name if ss_company else None,
                    error_type=result.error_type,
                    created_at=result.created_at,
                    is_downloaded=True,
                )
            )
        else:
            company_downloaded = db.exec(
                select(TeamCompany).where(
                    TeamCompany.corporate_number == result.ss_company_id
                )
            ).all()
            data.append(
                SalesforcePushErrorLogItem(
                    id=result.id,
                    ss_corporate_number=result.ss_company_id,
                    ss_company_name=ss_company.name if ss_company else None,
                    error_type=result.error_type,
                    created_at=result.created_at,
                    is_downloaded=len(company_downloaded) > 0,
                )
            )

    return ListingSalesforcePushErrorLogsResponse(
        data=data, per_page=per_page, page=page, total=total
    )


def listing_salesforce_push_error_log_detail(
    db: Session,
    current_user: UserBase,
    error_log_id: int,
    listing_plan_code: PlanCode,
) -> SalesforcePushErrorLogDetailResponse:
    sf_connection = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == current_user.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    if not sf_connection:
        raise NotFoundException(detail="common.notFound")

    result = db.exec(
        select(SalesforceCompanyPushHistories).where(
            SalesforceCompanyPushHistories.id == error_log_id,
            SalesforceCompanyPushHistories.team_id == current_user.team_id,
            SalesforceCompanyPushHistories.salesforce_integration_id
            == sf_connection.id,
            SalesforceCompanyPushHistories.salesforce_team_id
            == sf_connection.salesforce_team_id,
            SalesforceCompanyPushHistories.deleted_at.is_(None),
        )
    ).first()

    if not result:
        raise NotFoundException(detail="common.notFound")

    ss_company = db.exec(
        select(Company).where(
            Company.corporate_number == result.ss_company_id,
            Company.deleted_at.is_(None),
        )
    ).first()

    if not select:
        raise NotFoundException(detail="common.notFoundCompany")

    if listing_plan_code != PlanCode.UNLIMITED:
        company_downloaded = db.exec(
            select(TeamCompany).where(
                TeamCompany.corporate_number == result.ss_company_id
            )
        ).all()
        downloaded_flag = len(company_downloaded) > 0
    else:
        downloaded_flag = True

    if result.error_type == "MULTIPLE":
        data = []
        salesforce_client = SalesforceService(
            access_token=sf_connection.access_token,
            refresh_token=sf_connection.refresh_token,
            instance_url=sf_connection.instance_url,
            id_url=sf_connection.id_url,
        )

        salesforce_company_ids = db.exec(
            select(SalesforceCompanyMultiplePushHistories.matched_company_ids).where(
                SalesforceCompanyMultiplePushHistories.salesforce_push_history_id
                == error_log_id
            )
        ).first()

        multiple_companies = salesforce_client.get_companies_by_ids(
            company_ids=list(salesforce_company_ids) if salesforce_company_ids else [],
        )

        if len(multiple_companies) > 0:
            data = [
                SalesforcePushErrorLogCompany(
                    salesforce_company_id=company.get("Id"),
                    salesforce_company_name=company.get("Name"),
                    domain=company.get("Website"),
                )
                for company in multiple_companies
            ]

        return SalesforcePushErrorLogDetailResponse(
            total=len(multiple_companies),
            ss_corporate_number=result.ss_company_id,
            ss_company_name=ss_company.name,
            is_downloaded=downloaded_flag,
            created_at=result.created_at,
            error_type=result.error_type,
            data=data,
        )

    return SalesforcePushErrorLogDetailResponse(
        total=0,
        ss_corporate_number=result.ss_company_id,
        ss_company_name=ss_company.name,
        is_downloaded=downloaded_flag,
        created_at=result.created_at,
        error_type=result.error_type,
        data=[],
    )
