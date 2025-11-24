from typing import Optional

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from sqlmodel import Session

from app.api.v1.schemas.elasticsearch.persons_extend import ESPersonExtend
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.persons.build_search_query_by_search_conditions import (
    build_search_query_by_seach_conditions,
)


def statistics_persons(
    search_condition: Optional[SearchCrossRequest],
    db: Session,
    es_client: Elasticsearch,
    current_user: UserBase,
):
    search = ESPersonExtend.search(using=es_client, index=ESPersonExtend.Index.name)
    search_query = build_search_query_by_seach_conditions(
        search_condition, current_user, db
    )
    search: Search = search.query(search_query)  # Set condition before data query

    columns = ["linkedin_url", "twitter_url", "github_url", "fb_url", "wantedly_url"]

    for column in columns:
        search.aggs.metric(column, "value_count", field=column)

    search.aggs.metric("total", "value_count", field="uuid")
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
