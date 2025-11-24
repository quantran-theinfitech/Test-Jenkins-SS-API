from typing import Optional

from elasticsearch_dsl import Q, Search
from sqlalchemy.sql import text
from sqlmodel import Session

from app.api.v1.queries.company import build_es_query
from app.api.v1.schemas.elasticsearch.companies_extend import EsCompanyExtend
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase
from utils.custom_sorting import custom_sorting


def listing_companies_by_team_id(
    db: Session,
    search_condition: Optional[SearchCrossRequest],
    es_client,
    page: int,
    per_page: int,
    current_user: UserBase,
):
    search = EsCompanyExtend.search(using=es_client, index=EsCompanyExtend.Index.name)
    search_query = []

    query = """
            SELECT tc.corporate_number
            FROM team_companies tc
            LEFT JOIN companies c ON tc.corporate_number = c.corporate_number
            WHERE tc.team_id = :team_id"""

    corporate_numbers_downloaded = db.execute(
        text(query),
        {
            "team_id": current_user.team_id,
        },
    ).all()

    # if not is_null:
    corporate_numbers_by_tags = []
    if search_condition.tags and len(search_condition.tags) > 0:
        tag_query = """
                SELECT tc.corporate_number
                FROM team_companies tc
                WHERE tc.team_id = :team_id
                    AND tags && :tags
                """
        corporate_numbers_by_tags = db.execute(
            text(tag_query),
            {
                "team_id": current_user.team_id,
                "tags": "{{{}}}".format(
                    ", ".join(f'"{item}"' for item in set(search_condition.tags))
                ),
            },
        ).all()

    search_query = build_es_query(
        search_condition,
        ["".join(corporate_number) for corporate_number in corporate_numbers_by_tags],
        [
            "".join(corporate_number)
            for corporate_number in corporate_numbers_downloaded
        ],
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

    search = custom_sorting(search, search_condition)

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
    companies = [x["_source"] for x in data]

    return companies, total, unlimited_total
