from typing import Optional

from sqlmodel import Session, and_, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.integration.salesforce import (
    ListingSalesforcePullErrorLogsResponse,
    SalesforcePullErrorLogCompany,
    SalesforcePullErrorLogDetailResponse,
    SalesforcePullErrorLogItem,
)
from app.api.v1.schemas.users import UserBase
from app.models import (
    Company,
    SalesforceCompanyMultiplePullHistories,
    SalesforceCompanyPullHistories,
    SalesforceIntegrations,
    SalesforceRawCompanies,
    SalesforceSyncedCompanies,
    SalesforceSyncHistories,
    TeamCompany,
)
from app.models.team import PlanCode
from utils.extract_domain import extract_full_domain_url


def listing_salesforce_pull_error_logs(
    db: Session,
    current_user: UserBase,
    per_page: Optional[int] = None,
    page: Optional[int] = None,
) -> ListingSalesforcePullErrorLogsResponse:
    sf_connection = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == current_user.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    if not sf_connection:
        raise NotFoundException(detail="common.notFound")

    total = (
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

    query = (
        select(SalesforceCompanyPullHistories, SalesforceRawCompanies)
        .join(
            SalesforceSyncHistories,
            and_(
                SalesforceSyncHistories.log_id == SalesforceCompanyPullHistories.log_id,
                SalesforceSyncHistories.deleted_at.is_(None),
            ),
        )
        .join(
            SalesforceRawCompanies,
            and_(
                SalesforceRawCompanies.salesforce_integration_id == sf_connection.id,
                SalesforceRawCompanies.salesforce_team_id
                == sf_connection.salesforce_team_id,
                SalesforceRawCompanies.salesforce_company_id
                == SalesforceCompanyPullHistories.salesforce_company_id,
                SalesforceRawCompanies.deleted_at.is_(None),
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
        .order_by(
            SalesforceCompanyPullHistories.salesforce_company_id,
            SalesforceCompanyPullHistories.created_at.desc(),
        )
    )

    if page is not None and per_page is not None:
        query = query.offset((page - 1) * per_page).limit(per_page)

    results = db.exec(query).all()

    result_dict = [
        {
            "salesforce_company_pull_histories": history.dict(),
            "salesforce_raw_companies": raw_company.dict(),
        }
        for history, raw_company in results
    ]

    data = []
    for log in result_dict:
        salesforce_company_pull_histories = log.get(
            "salesforce_company_pull_histories", {}
        )
        salesforce_raw_companies = log.get("salesforce_raw_companies", {})
        salesforce_company_id = salesforce_company_pull_histories.get(
            "salesforce_company_id"
        )
        url = ""
        if sf_connection.instance_url and salesforce_company_id:
            if sf_connection.instance_url.endswith("/"):
                url = sf_connection.instance_url + salesforce_company_id
            else:
                url = sf_connection.instance_url + "/" + salesforce_company_id
        data.append(
            SalesforcePullErrorLogItem(
                id=salesforce_company_pull_histories.get("id") or 0,
                salesforce_team_id=sf_connection.salesforce_team_id,
                salesforce_company_id=salesforce_company_id,
                salesforce_company_name=salesforce_raw_companies.get("data", {}).get(
                    "Name"
                )
                or None,
                error_type=salesforce_company_pull_histories.get("error_type"),
                created_at=salesforce_company_pull_histories.get("created_at"),
                url=url,
            )
        )

    return ListingSalesforcePullErrorLogsResponse(
        data=data,
        total=total,
        page=page,
        per_page=per_page,
    )


def listing_salesforce_pull_error_log_detail(
    error_log_id: int,
    db: Session,
    current_user: UserBase,
    listing_plan_code: PlanCode,
) -> SalesforcePullErrorLogDetailResponse:
    sf_connection = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == current_user.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    if not sf_connection:
        raise NotFoundException(detail="common.notFound")

    result = db.exec(
        select(SalesforceCompanyPullHistories, SalesforceRawCompanies)
        .join(
            SalesforceRawCompanies,
            and_(
                SalesforceRawCompanies.salesforce_integration_id == sf_connection.id,
                SalesforceRawCompanies.salesforce_team_id
                == sf_connection.salesforce_team_id,
                SalesforceRawCompanies.salesforce_company_id
                == SalesforceCompanyPullHistories.salesforce_company_id,
                SalesforceRawCompanies.deleted_at.is_(None),
            ),
        )
        .where(
            SalesforceCompanyPullHistories.id == error_log_id,
            SalesforceCompanyPullHistories.team_id == current_user.team_id,
            SalesforceCompanyPullHistories.salesforce_integration_id
            == sf_connection.id,
            SalesforceCompanyPullHistories.salesforce_team_id
            == sf_connection.salesforce_team_id,
            SalesforceCompanyPullHistories.deleted_at.is_(None),
        )
    ).first()

    if not result:
        raise NotFoundException(detail="common.notFound")

    pull_history, raw_company = result

    if not pull_history:
        raise NotFoundException(detail="common.notFound")

    url = ""
    if sf_connection.instance_url and pull_history.salesforce_company_id:
        if sf_connection.instance_url.endswith("/"):
            url = sf_connection.instance_url + pull_history.salesforce_company_id
        else:
            url = sf_connection.instance_url + "/" + pull_history.salesforce_company_id

    if pull_history.error_type == "MULTIPLE":
        data = []
        detail = db.exec(
            select(SalesforceCompanyMultiplePullHistories).where(
                SalesforceCompanyMultiplePullHistories.salesforce_pull_history_id
                == error_log_id,
                SalesforceCompanyMultiplePullHistories.deleted_at.is_(None),
            )
        ).first()

        if not detail:
            raise NotFoundException(detail="common.notFound")
        if detail.matched_company_ids and len(detail.matched_company_ids) > 0:
            for corporate_number in detail.matched_company_ids:
                ss_company = db.exec(
                    select(Company).where(Company.corporate_number == corporate_number)
                ).first()

                domain_url = extract_full_domain_url(ss_company.hp_url)
                if domain_url:
                    favicon_url = f"{domain_url}/favicon.ico"
                else:
                    favicon_url = None

                if listing_plan_code == PlanCode.UNLIMITED:
                    data.append(
                        SalesforcePullErrorLogCompany(
                            ss_corporate_number=corporate_number,
                            ss_company_name=ss_company.name,
                            domain=ss_company.domain,
                            is_downloaded=True,
                            favicon_url=favicon_url,
                            president_name=ss_company.president_name,
                        )
                    )
                else:
                    corporate_numbers_downloaded = db.exec(
                        select(TeamCompany.corporate_number).where(
                            TeamCompany.corporate_number == corporate_number,
                            TeamCompany.deleted_at.is_(None),
                            TeamCompany.team_id == current_user.team_id,
                        )
                    ).all()

                    is_downloaded = len(corporate_numbers_downloaded) > 0
                    data.append(
                        SalesforcePullErrorLogCompany(
                            ss_corporate_number=corporate_number,
                            ss_company_name=ss_company.name,
                            domain=ss_company.domain,
                            is_downloaded=is_downloaded,
                            favicon_url=favicon_url,
                            president_name=ss_company.president_name,
                        )
                    )

        return SalesforcePullErrorLogDetailResponse(
            total=len(data),
            salesforce_company_id=pull_history.salesforce_company_id,
            salesforce_company_name=raw_company.data.get("Name")
            if raw_company.data
            else None,
            error_type=pull_history.error_type,
            created_at=pull_history.created_at,
            data=data,
            url=url,
        )

    return SalesforcePullErrorLogDetailResponse(
        total=0,
        salesforce_company_id=pull_history.salesforce_company_id,
        salesforce_company_name=raw_company.data.get("Name")
        if raw_company.data
        else None,
        error_type=pull_history.error_type,
        created_at=pull_history.created_at,
        data=[],
        url=url,
    )
