from typing import Optional

from sqlmodel import Session, and_, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.hubspot_connections import (
    HubspotManualIdentifyLogs,
    HubspotManualPullLogs,
    HubspotManualPushLogs,
    ListingHubspotManualIdentifyLogs,
    ListingHubspotManualPullLogs,
    ListingHubspotManualPushLogs,
)
from app.api.v1.schemas.users import UserBase
from app.models import (
    HubspotCompanyPullHistories,
    HubspotCompanyPushHistories,
    HubspotCompanySyncHistories,
    HubspotIntergrations,
    HubspotPullPersonHistories,
    TeamCompany,
)
from app.models.company import Company
from app.models.integration.hubspot.hubspot_raw_companies import HubspotRawCompanies
from app.models.integration.hubspot.hubspot_raw_persons import HubspotRawPersons
from app.models.integration.hubspot.hubspot_synced_companies import (
    HubspotSyncedCompanies,
)
from app.models.team import PlanCode


def listing_hubspot_manual_push_log(
    db: Session,
    listing_plan_code: PlanCode,
    current_user: UserBase,
    per_page: Optional[int] = None,
    page: Optional[int] = None,
):
    # Lấy thông tin kết nối HubSpot
    hubspot_connection = db.exec(
        select(HubspotIntergrations).where(
            HubspotIntergrations.team_id == current_user.team_id,
            HubspotIntergrations.deleted_at.is_(None),
        )
    ).first()

    if not hubspot_connection:
        raise NotFoundException(detail="integration.hubspot.notFoundConnection")

    total_query = (
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

    total = total_query.count()

    query = (
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
        .order_by(
            HubspotCompanyPushHistories.ss_company_id,
            HubspotCompanyPushHistories.created_at.desc(),
        )
    )

    if page is not None and per_page is not None:
        query = query.offset((page - 1) * per_page)
        query = query.limit(per_page)

    list_manual_push_log = query.all()

    data = []
    for log in list_manual_push_log:
        ss_company = db.exec(
            select(Company).where(Company.corporate_number == log.ss_company_id)
        ).first()
        if listing_plan_code == PlanCode.UNLIMITED:
            data.append(
                HubspotManualPushLogs(
                    id=log.id,
                    ss_corporate_number=log.ss_company_id,
                    ss_company_name=ss_company.name,
                    error_type=log.error_type,
                    created_at=log.created_at,
                    is_downloaded=True,
                )
            )
        else:
            company_downloaded = db.exec(
                select(TeamCompany).where(
                    TeamCompany.corporate_number == log.ss_company_id
                )
            ).all()
            is_downloaded = len(company_downloaded) > 0
            data.append(
                HubspotManualPushLogs(
                    id=log.id,
                    ss_corporate_number=log.ss_company_id,
                    ss_company_name=ss_company.name,
                    error_type=log.error_type,
                    created_at=log.created_at,
                    is_downloaded=is_downloaded,
                )
            )

    return ListingHubspotManualPushLogs(
        per_page=per_page, page=page, total=total, data=data
    )


def listing_hubspot_manual_pull_log(
    db: Session,
    current_user: UserBase,
    per_page: Optional[int] = None,
    page: Optional[int] = None,
):
    # Lấy thông tin kết nối HubSpot
    hubspot_connection = db.exec(
        select(HubspotIntergrations).where(
            HubspotIntergrations.team_id == current_user.team_id,
            HubspotIntergrations.deleted_at.is_(None),
        )
    ).first()

    if not hubspot_connection:
        raise NotFoundException(detail="integration.hubspot.notFoundConnection")

    total_query = (
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
    total = total_query.count()

    query = (
        db.query(HubspotCompanyPullHistories, HubspotRawCompanies)
        .join(
            HubspotCompanySyncHistories,
            and_(
                HubspotCompanySyncHistories.log_id
                == HubspotCompanyPullHistories.log_id,
                HubspotCompanySyncHistories.deleted_at.is_(None),
            ),
        )
        .join(
            HubspotRawCompanies,
            and_(
                HubspotRawCompanies.integration_id == hubspot_connection.id,
                HubspotRawCompanies.hubspot_team_id
                == hubspot_connection.hubspot_team_id,
                HubspotRawCompanies.hubspot_company_id
                == HubspotCompanyPullHistories.hubspot_company_id,
                HubspotRawCompanies.deleted_at.is_(None),
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
        .order_by(
            HubspotCompanyPullHistories.hubspot_company_id,
            HubspotCompanyPullHistories.created_at.desc(),
        )
    )

    if page is not None and per_page is not None:
        query = query.offset((page - 1) * per_page)
        query = query.limit(per_page)

    list_manual_pull_log = query.all()

    result_dict = [
        {
            "hubspot_company_pull_histories": history.dict(),
            "hubspot_raw_companies": raw_company.dict(),
        }
        for history, raw_company in list_manual_pull_log
    ]

    data = []

    for log in result_dict:
        hubspot_company_pull_histories = log.get("hubspot_company_pull_histories", {})
        hubspot_raw_companies = log.get("hubspot_raw_companies", {})
        data.append(
            HubspotManualPullLogs(
                id=hubspot_company_pull_histories.get("id"),
                hubspot_team_id=str(hubspot_connection.hubspot_team_id),
                hubspot_company_id=hubspot_raw_companies.get("hubspot_company_id"),
                hub_company_name=hubspot_raw_companies.get("data").get("name") or None,
                error_type=hubspot_company_pull_histories.get("error_type"),
                created_at=hubspot_company_pull_histories.get("created_at"),
            )
        )

    return ListingHubspotManualPullLogs(
        per_page=per_page, page=page, total=total, data=data
    )


def listing_hubspot_manual_identify_log(
    db: Session,
    current_user: UserBase,
    per_page: Optional[int] = None,
    page: Optional[int] = None,
):
    # Lấy thông tin kết nối HubSpot
    hubspot_connection = db.exec(
        select(HubspotIntergrations).where(
            HubspotIntergrations.team_id == current_user.team_id,
            HubspotIntergrations.deleted_at.is_(None),
        )
    ).first()

    if not hubspot_connection:
        raise NotFoundException(detail="integration.hubspot.notFoundConnection")

    total_query = (
        db.query(HubspotPullPersonHistories)
        .join(
            HubspotCompanySyncHistories,
            and_(
                HubspotCompanySyncHistories.log_id == HubspotPullPersonHistories.log_id,
                HubspotCompanySyncHistories.deleted_at.is_(None),
            ),
        )
        .outerjoin(
            HubspotSyncedCompanies,
            and_(
                HubspotSyncedCompanies.hubspot_company_id
                == HubspotPullPersonHistories.hubspot_company_id,
                HubspotSyncedCompanies.integration_id == hubspot_connection.id,
                HubspotSyncedCompanies.deleted_at.is_(None),
            ),
        )
        .filter(
            HubspotCompanySyncHistories.integration_id == hubspot_connection.id,
            HubspotCompanySyncHistories.hubspot_team_id
            == hubspot_connection.hubspot_team_id,
            HubspotPullPersonHistories.deleted_at.is_(None),
            HubspotPullPersonHistories.error_type.isnot(None),
            HubspotSyncedCompanies.id.is_(None),
        )
        .distinct(HubspotPullPersonHistories.hubspot_person_id)
    )
    total = total_query.count()

    query = (
        db.query(HubspotPullPersonHistories, HubspotRawPersons)
        .join(
            HubspotCompanySyncHistories,
            and_(
                HubspotCompanySyncHistories.log_id == HubspotPullPersonHistories.log_id,
                HubspotCompanySyncHistories.deleted_at.is_(None),
            ),
        )
        .join(
            HubspotRawPersons,
            and_(
                HubspotRawPersons.integration_id == hubspot_connection.id,
                HubspotRawPersons.hubspot_team_id == hubspot_connection.hubspot_team_id,
                HubspotRawPersons.hubspot_person_id
                == HubspotPullPersonHistories.hubspot_person_id,
                HubspotRawPersons.deleted_at.is_(None),
            ),
        )
        .outerjoin(
            HubspotSyncedCompanies,
            and_(
                HubspotSyncedCompanies.hubspot_company_id
                == HubspotPullPersonHistories.hubspot_company_id,
                HubspotSyncedCompanies.integration_id == hubspot_connection.id,
                HubspotSyncedCompanies.deleted_at.is_(None),
            ),
        )
        .filter(
            HubspotCompanySyncHistories.integration_id == hubspot_connection.id,
            HubspotCompanySyncHistories.hubspot_team_id
            == hubspot_connection.hubspot_team_id,
            HubspotPullPersonHistories.deleted_at.is_(None),
            HubspotPullPersonHistories.error_type.isnot(None),
            HubspotSyncedCompanies.id.is_(None),
        )
        .distinct(HubspotPullPersonHistories.hubspot_person_id)
        .order_by(
            HubspotPullPersonHistories.hubspot_person_id,
            HubspotPullPersonHistories.created_at.desc(),
        )
    )

    if page is not None and per_page is not None:
        query = query.offset((page - 1) * per_page)
        query = query.limit(per_page)

    list_manual_pull_log = query.all()

    result_dict = [
        {
            "hubspot_person_pull_histories": history.dict(),
            "hubspot_raw_persoms": person.dict(),
        }
        for history, person in list_manual_pull_log
    ]

    data = []

    for log in result_dict:
        hubspot_person_pull_histories = log.get("hubspot_person_pull_histories", {})
        hubspot_raw_persoms = log.get("hubspot_raw_persoms", {})
        data.append(
            HubspotManualIdentifyLogs(
                id=hubspot_person_pull_histories.get("id"),
                hubspot_team_id=str(hubspot_connection.hubspot_team_id),
                hubspot_person_id=hubspot_person_pull_histories.get(
                    "hubspot_person_id"
                ),
                hub_person_name=hubspot_raw_persoms.get("data").get("firstname")
                or None,
                error_type=hubspot_person_pull_histories.get("error_type"),
                created_at=hubspot_person_pull_histories.get("created_at"),
            )
        )

    return ListingHubspotManualIdentifyLogs(
        per_page=per_page, page=page, total=total, data=data
    )
