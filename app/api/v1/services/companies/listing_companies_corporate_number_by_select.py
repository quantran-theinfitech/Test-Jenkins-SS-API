from typing import List, Optional

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Search
from sqlmodel import Session, func, select

from app.api.v1.schemas.elasticsearch.companies_extend import EsCompanyExtend
from app.api.v1.schemas.search_companies import GetTotalCompanyLockAndUnlockResponse
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.companies.build_search_query_by_seach_conditions import (
    build_search_query_by_seach_conditions,
)
from app.constant.constants import INTEGRATION_PLATFORM_ENUM
from app.models.integration.hubspot.hubspot_integrations import HubspotIntergrations
from app.models.integration.hubspot.hubspot_synced_companies import (
    HubspotSyncedCompanies,
)
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from app.models.integration.salesforce.salesforce_synced_companies import (
    SalesforceSyncedCompanies,
)
from app.models.team import PlanCode, Team
from app.models.team_company import TeamCompany
from utils.custom_sorting import custom_sorting


def listing_companies_corporate_number_by_select(
    db: Session,
    search_condition: Optional[SearchCrossRequest],
    es_client: Elasticsearch,
    page: int,
    per_page: int,
    current_user: UserBase,
):
    search = EsCompanyExtend.search(using=es_client, index=EsCompanyExtend.Index.name)

    search_query = build_search_query_by_seach_conditions(
        search_condition=search_condition, current_user=current_user, db=db
    )

    exist_query = [
        {"exists": {"field": "name", "boost": 2}},
        {"exists": {"field": "hp_url", "boost": 2}},
        {"exists": {"field": "contact_form_url", "boost": 1.95}},
        {"exists": {"field": "phone", "boost": 1.9}},
        {"exists": {"field": "contact_email", "boost": 1.85}},
        {"exists": {"field": "recruit_phone", "boost": 1.8}},
        {"exists": {"field": "recruit_email", "boost": 1.75}},
        {"exists": {"field": "president_name", "boost": 1.7}},
        {"exists": {"field": "establish_at", "boost": 1.65}},
    ]
    search_query = Q(
        "bool", must=search_query, should=exist_query, minimum_should_match=0
    )
    search: Search = search.query(search_query)
    # By default elasticsearch sorts by timestamp so when updating,
    # the location will be changed
    search = custom_sorting(search, search_condition)

    search = search.params(request_timeout=30)
    if search_condition and search_condition.is_default_filter:
        search = search.params(request_cache=True)

    pagination_param = {
        "size": per_page,
        "from": 0,
        "track_total_hits": False,
    }

    pagination_param["_source"] = ["corporate_number"]
    result = search.extra(**pagination_param).execute()["hits"]

    data = result["hits"]._l_
    companies = [x["_source"] for x in data]

    corporate_numbers = [x["corporate_number"] for x in companies]

    return corporate_numbers


def get_total_lock_unlock_companies_service(
    db: Session,
    corporate_numbers: List,
    listing_plan_code: PlanCode,
    current_user: UserBase,
):
    total = len(corporate_numbers) if corporate_numbers else 0
    total_synced_companies = 0

    team = db.exec(select(Team).where(Team.id == current_user.team_id)).first()

    if team and team.integrated_platform:
        if team.integrated_platform == INTEGRATION_PLATFORM_ENUM["SALESFORCE"]:
            salesforce_integration = db.exec(
                select(SalesforceIntegrations)
                .where(SalesforceIntegrations.team_id == team.id)
                .where(SalesforceIntegrations.deleted_at.is_(None))
            ).first()

            total_synced_companies = db.exec(
                select(
                    func.count(
                        func.distinct(SalesforceSyncedCompanies.ss_company_id)
                    ).label("total_synced_companies")
                )
                .where(SalesforceSyncedCompanies.ss_company_id.in_(corporate_numbers))
                .where(
                    SalesforceSyncedCompanies.salesforce_team_id
                    == salesforce_integration.salesforce_team_id
                )
                .where(
                    SalesforceSyncedCompanies.salesforce_integration_id
                    == salesforce_integration.id
                )
                .where(SalesforceSyncedCompanies.deleted_at.is_(None))
            ).first()
        elif team.integrated_platform == INTEGRATION_PLATFORM_ENUM["HUBSPOT"]:
            hubspot_integration = db.exec(
                select(HubspotIntergrations)
                .where(HubspotIntergrations.team_id == team.id)
                .where(HubspotIntergrations.deleted_at.is_(None))
            ).first()

            total_synced_companies = db.exec(
                select(
                    func.count(
                        func.distinct(HubspotSyncedCompanies.ss_company_id)
                    ).label("total_synced_companies")
                )
                .where(HubspotSyncedCompanies.ss_company_id.in_(corporate_numbers))
                .where(
                    HubspotSyncedCompanies.hubspot_team_id
                    == hubspot_integration.hubspot_team_id
                )
                .where(HubspotSyncedCompanies.integration_id == hubspot_integration.id)
                .where(HubspotSyncedCompanies.deleted_at.is_(None))
            ).first()

    if listing_plan_code == PlanCode.UNLIMITED:
        return GetTotalCompanyLockAndUnlockResponse(
            total=total,
            total_lock=0,
            total_unlock=total,
            total_push_companies=total - total_synced_companies,
        )

    result = db.exec(
        select(
            func.count(func.distinct(TeamCompany.corporate_number)).label(
                "total_unlock"
            )
        )
        .where(TeamCompany.team_id == current_user.team_id)
        .where(TeamCompany.corporate_number.in_(corporate_numbers))
    ).first()

    total_unlock = result if result else 0
    return GetTotalCompanyLockAndUnlockResponse(
        total=total,
        total_lock=total - total_unlock,
        total_unlock=total_unlock,
        total_push_companies=total - total_synced_companies,
    )
