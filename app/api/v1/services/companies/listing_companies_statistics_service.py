from typing import Optional

from elasticsearch_dsl import Search
from sqlmodel import Session

from app.api.v1.schemas.elasticsearch.companies_extend import EsCompanyExtend
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.companies.build_search_query_by_seach_conditions import (
    build_search_query_by_seach_conditions,
)


def listing_companies_statistics(
    db: Session,
    search_condition: Optional[SearchCrossRequest],
    es_client,
    current_user: UserBase,
):
    search = EsCompanyExtend.search(using=es_client, index=EsCompanyExtend.Index.name)
    search_query = build_search_query_by_seach_conditions(
        search_condition=search_condition, current_user=current_user, db=db
    )
    search: Search = search.query(search_query)  # Set condition before data query

    columns = [
        "phone",
        "contact_email",
        "recruit_phone",
        "recruit_email",
        "contact_form_url",
        "hp_url",
    ]

    for column in columns:
        search.aggs.metric(column, "value_count", field=column)

    # Count all
    search.aggs.metric("total", "value_count", field="corporate_number")
    if search_condition and search_condition.is_default_filter:
        search = search.params(request_cache=True)

    response = search.extra(size=0).execute()  # Data query (.execute(), .count(), ...)

    result = {}

    for column in columns:
        result[column] = response.aggregations[column].value

    result["unlimited_total"] = response.aggregations["total"].value
    result["total"] = (
        result["unlimited_total"] if result["unlimited_total"] < 10000 else 10000
    )

    return result
