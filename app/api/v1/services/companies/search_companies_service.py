from typing import Optional

from elasticsearch_dsl import Q, Search
from sqlmodel import Session, col, select

from app.api.v1.schemas.elasticsearch.companies_extend import EsCompanyExtend
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.companies.build_search_query_by_seach_conditions import (
    build_search_query_by_seach_conditions,
)
from app.models import TeamCompany
from app.models.team import PlanCode
from utils.custom_sorting import custom_sorting
from utils.mask_company_data import mask_company_data


def search_companies(
    db: Session,
    search_condition: Optional[SearchCrossRequest],
    es_client,
    page: int,
    per_page: int,
    listing_plan_code: PlanCode,
    current_user: UserBase,
    is_select: bool = False,
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

    size = 0
    if (10000 - ((page - 1) * per_page)) < 15:
        size = 10000 - ((page - 1) * per_page)
    else:
        size = per_page

    pagination_param = {
        "size": size,
        "from": (page - 1) * per_page,
        "track_total_hits": False,
    }

    if is_select:
        pagination_param["_source"] = ["corporate_number"]
    else:
        source_fields = [
            "name",
            "corporate_number",
            "downloaded_flag",
            "industry_code",
            "president_name",
            "establish_at",
            "listing_market_code",
            "phone",
            "recruit_email",
            "contact_email",
            "hp_url",
            "contact_form_url",
            "original_tags",
        ]

        if (
            search_condition
            and search_condition.sorting
            and search_condition.sorting.field
        ):
            sort_field = search_condition.sorting.field.value.lower()
            if sort_field not in source_fields:
                source_fields.append(sort_field)

        pagination_param["_source"] = source_fields

    result = search.extra(**pagination_param).execute()["hits"]

    data = result["hits"]._l_
    companies = [x["_source"] for x in data]
    corporate_numbers = [x["corporate_number"] for x in companies]

    if listing_plan_code == PlanCode.UNLIMITED:
        for company in companies:
            company["downloaded_flag"] = True
        return companies, 0, 0

    corporate_numbers_downloaded = db.exec(
        select(TeamCompany.corporate_number)
        .where(TeamCompany.team_id == current_user.team_id)
        .where(col(TeamCompany.corporate_number).in_(corporate_numbers))
    ).all()

    new_companies = mask_company_data(companies, corporate_numbers_downloaded)

    return new_companies, 0, 0
