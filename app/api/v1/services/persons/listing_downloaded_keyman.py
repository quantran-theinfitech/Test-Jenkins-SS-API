from typing import Optional

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Search
from sqlalchemy.sql import text
from sqlmodel import Session

from app.api.v1.queries.person import build_es_query
from app.api.v1.schemas.elasticsearch.persons_extend import ESPersonExtend
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase


def listing_downloaded_keyman(
    db: Session,
    search_condition: Optional[SearchCrossRequest],
    es_client: Elasticsearch,
    page: int,
    per_page: int,
    current_user: UserBase,
):

    query = """
            SELECT tp.person_uuid FROM team_persons tp
            LEFT JOIN persons p
            ON tp.person_uuid = p.uuid
            WHERE tp.team_id = :team_id
            """

    persons = db.execute(
        text(query),
        {
            "team_id": current_user.team_id,
        },
    ).all()

    search = ESPersonExtend.search(using=es_client, index=ESPersonExtend.Index.name)
    search_query = []
    search_query = build_es_query(
        search_condition,
        ["".join(person_uuid) for person_uuid in persons],
    )

    ranking_query = [
        {"exists": {"field": "name", "boost": 2}},
        {"exists": {"field": "linkedin_url", "boost": 2}},
        {"exists": {"field": "role_group_codes", "boost": 1.95}},
        {
            "terms": {
                "role_group_codes": [
                    "社長",
                    "役員クラス",
                    "経営企画",
                    "責任者クラス",
                    "事業企画/事業開発",
                    "プロジェクトマネジャー",
                    "営業",
                    "営業支援/営業企画",
                ],
                "boost": 1.95,
            }
        },
        {"exists": {"field": "wantedly_url", "boost": 1.9}},
        {"exists": {"field": "address", "boost": 1.85}},
        {
            "regexp": {
                "name": {
                    "value": "[ぁ-んァ-ン一-龥]",
                    "flags": "ALL",
                    "case_insensitive": True,
                    "max_determinized_states": 10000,
                    "rewrite": "constant_score",
                    "boost": 1.8,
                }
            }
        },
    ]

    search_query = Q(
        "bool", must=search_query, should=ranking_query, minimum_should_match=0
    )

    search: Search = search.query(search_query)
    # By default elasticsearch sorts by timestamp so when updating,
    # the location will be changed
    search = search.sort("_score", "_id")
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

    result = search.extra(**pagination_param).execute()["hits"]
    data = result["hits"]._l_
    unlimited_total = result._d_["total"]["value"]
    total = unlimited_total if unlimited_total <= 10000 else 10000
    persons = [x["_source"] for x in data]

    return persons, total, unlimited_total
