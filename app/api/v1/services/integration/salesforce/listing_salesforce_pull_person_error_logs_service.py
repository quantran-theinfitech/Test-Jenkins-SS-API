from typing import Optional

from sqlmodel import Session, and_, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.integration.salesforce import (
    ListingSalesforcePullPersonErrorLogsResponse,
    SalesforcePullPersonErrorLog,
    SalesforcePullPersonErrorLogDetailResponse,
    SalesforcePullPersonErrorLogItem,
)
from app.api.v1.schemas.users import UserBase
from app.models import (
    SalesforceIntegrations,
    SalesforcePersonMultiplePullHistories,
    SalesforcePersonPullHistories,
    SalesforceRawPersons,
    SalesforceSyncHistories,
)
from app.models.company import Company
from app.models.team import PlanCode
from app.models.team_company import TeamCompany
from utils.extract_domain import extract_full_domain_url


def listing_salesforce_pull_person_error_logs(
    db: Session,
    current_user: UserBase,
    per_page: Optional[int] = None,
    page: Optional[int] = None,
) -> ListingSalesforcePullPersonErrorLogsResponse:
    sf_connection = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == current_user.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    if not sf_connection:
        raise NotFoundException(detail="common.notFound")

    total = (
        db.query(SalesforcePersonPullHistories)
        .join(
            SalesforceSyncHistories,
            and_(
                SalesforceSyncHistories.log_id == SalesforcePersonPullHistories.log_id,
                SalesforceSyncHistories.deleted_at.is_(None),
            ),
        )
        .where(
            SalesforceSyncHistories.salesforce_integration_id == sf_connection.id,
            SalesforceSyncHistories.salesforce_team_id
            == sf_connection.salesforce_team_id,
            SalesforceSyncHistories.team_id == current_user.team_id,
            SalesforcePersonPullHistories.deleted_at.is_(None),
            SalesforcePersonPullHistories.error_type.isnot(None),
        )
        .distinct(SalesforcePersonPullHistories.salesforce_person_id)
        .count()
    )

    query = (
        select(SalesforcePersonPullHistories, SalesforceRawPersons)
        .join(
            SalesforceSyncHistories,
            and_(
                SalesforceSyncHistories.log_id == SalesforcePersonPullHistories.log_id,
                SalesforceSyncHistories.deleted_at.is_(None),
            ),
        )
        .join(
            SalesforceRawPersons,
            and_(
                SalesforceRawPersons.salesforce_integration_id == sf_connection.id,
                SalesforceRawPersons.salesforce_team_id
                == sf_connection.salesforce_team_id,
                SalesforceRawPersons.salesforce_person_id
                == SalesforcePersonPullHistories.salesforce_person_id,
                SalesforceRawPersons.deleted_at.is_(None),
            ),
        )
        .where(
            SalesforceSyncHistories.salesforce_integration_id == sf_connection.id,
            SalesforceSyncHistories.salesforce_team_id
            == sf_connection.salesforce_team_id,
            SalesforceSyncHistories.team_id == current_user.team_id,
            SalesforcePersonPullHistories.deleted_at.is_(None),
            SalesforcePersonPullHistories.error_type.isnot(None),
        )
        .distinct(SalesforcePersonPullHistories.salesforce_person_id)
        .order_by(
            SalesforcePersonPullHistories.salesforce_person_id,
            SalesforcePersonPullHistories.created_at.desc(),
        )
    )

    if page is not None and per_page is not None:
        query = query.offset((page - 1) * per_page).limit(per_page)

    results = db.exec(query).all()

    result_dict = [
        {
            "salesforce_person_pull_histories": history.dict(),
            "salesforce_raw_persons": person.dict(),
        }
        for history, person in results
    ]

    data = []

    for log in result_dict:
        salesforce_person_pull_histories = log.get(
            "salesforce_person_pull_histories", {}
        )
        salesforce_raw_persons = log.get("salesforce_raw_persons", {})
        salesforce_person_id = salesforce_person_pull_histories.get(
            "salesforce_person_id"
        )
        url = ""
        if sf_connection.instance_url and salesforce_person_id:
            if sf_connection.instance_url.endswith("/"):
                url = sf_connection.instance_url + salesforce_person_id
            else:
                url = sf_connection.instance_url + "/" + salesforce_person_id
        first_name = salesforce_raw_persons.get("data", {}).get("FirstName") or ""
        last_name = salesforce_raw_persons.get("data", {}).get("LastName") or ""
        salesforce_person_name = (first_name + " " + last_name).strip() or None
        data.append(
            SalesforcePullPersonErrorLogItem(
                id=salesforce_person_pull_histories.get("id"),
                salesforce_team_id=sf_connection.salesforce_team_id,
                salesforce_person_id=salesforce_person_id,
                salesforce_person_name=salesforce_person_name,
                error_type=salesforce_person_pull_histories.get("error_type"),
                created_at=salesforce_person_pull_histories.get("created_at"),
                url=url,
            )
        )
    return ListingSalesforcePullPersonErrorLogsResponse(
        per_page=per_page,
        page=page,
        total=total,
        data=data,
    )


def listing_salesforce_pull_person_error_log_detail(
    error_log_id: int,
    db: Session,
    current_user: UserBase,
    listing_plan_code: PlanCode,
) -> SalesforcePullPersonErrorLogDetailResponse:
    sf_connection = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == current_user.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    if not sf_connection:
        raise NotFoundException(detail="common.notFound")

    result = db.exec(
        select(SalesforcePersonPullHistories, SalesforceRawPersons)
        .join(
            SalesforceRawPersons,
            and_(
                SalesforceRawPersons.salesforce_integration_id == sf_connection.id,
                SalesforceRawPersons.salesforce_team_id
                == sf_connection.salesforce_team_id,
                SalesforceRawPersons.salesforce_person_id
                == SalesforcePersonPullHistories.salesforce_person_id,
                SalesforceRawPersons.deleted_at.is_(None),
            ),
        )
        .where(
            SalesforcePersonPullHistories.id == error_log_id,
            SalesforcePersonPullHistories.deleted_at.is_(None),
        )
    ).first()

    if not result:
        raise NotFoundException(detail="common.notFound")

    pull_history, raw_person = result

    if not pull_history:
        raise NotFoundException(detail="common.notFound")

    url = ""
    if sf_connection.instance_url and pull_history.salesforce_person_id:
        if sf_connection.instance_url.endswith("/"):
            url = sf_connection.instance_url + pull_history.salesforce_person_id
        else:
            url = sf_connection.instance_url + "/" + pull_history.salesforce_person_id

    if pull_history.error_type == "MULTIPLE":
        data = []
        detail = db.exec(
            select(SalesforcePersonMultiplePullHistories).where(
                SalesforcePersonMultiplePullHistories.salesforce_person_history_id
                == error_log_id,
                SalesforcePersonMultiplePullHistories.deleted_at.is_(None),
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
                        SalesforcePullPersonErrorLog(
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
                        SalesforcePullPersonErrorLog(
                            ss_corporate_number=corporate_number,
                            ss_company_name=ss_company.name,
                            domain=ss_company.domain,
                            is_downloaded=is_downloaded,
                            favicon_url=favicon_url,
                            president_name=ss_company.president_name,
                        )
                    )

        return SalesforcePullPersonErrorLogDetailResponse(
            total=len(data),
            salesforce_person_id=pull_history.salesforce_person_id,
            salesforce_person_name=(
                (
                    (raw_person.data.get("FirstName") or "")
                    + " "
                    + (raw_person.data.get("LastName") or "")
                ).strip()
                if raw_person.data
                else None
            ),
            error_type=pull_history.error_type,
            created_at=pull_history.created_at,
            url=url,
            data=data,
        )

    return SalesforcePullPersonErrorLogDetailResponse(
        error_type=pull_history.error_type,
        created_at=pull_history.created_at,
        salesforce_person_id=pull_history.salesforce_person_id,
        salesforce_person_name=(
            (
                (raw_person.data.get("FirstName") or "")
                + " "
                + (raw_person.data.get("LastName") or "")
            ).strip()
            if raw_person.data
            else None
        ),
        total=0,
        data=[],
        url=url,
    )
