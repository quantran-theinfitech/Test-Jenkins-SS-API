from typing import Optional

from elasticsearch_dsl import Q, Search

from app.api.v1.schemas.elasticsearch.original_tag import EsOriginalTag


def search_original_tag_team_company(
    tag: str,
    es_client,
    per_page: Optional[int],
    page: Optional[int],
):
    search: Search = EsOriginalTag.search(
        using=es_client, index=EsOriginalTag.Index.name
    )
    search_query = []
    if tag != "":
        search_query.append(Q("match", tag=tag))
    size = 0
    if (10000 - ((page - 1) * per_page)) < 15:
        size = 10000 - ((page - 1) * per_page)
    else:
        size = per_page

    pagination_param = {
        "size": size,
        "from": (page - 1) * per_page,
        "track_total_hits": True,
    }
    search_query = Q("bool", must=search_query)
    search = search.query(search_query).sort("_score", "_id")
    result = search.extra(**pagination_param).execute()
    return [hit.tag for hit in result]
