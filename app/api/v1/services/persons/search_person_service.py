import json
import os
from typing import Optional

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Search
from sqlalchemy import select
from sqlmodel import Session, col

from app.api.v1.schemas.elasticsearch.persons_extend import ESPersonExtend
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.persons.build_search_query_by_search_conditions import (
    build_search_query_by_seach_conditions,
)
from app.models import TeamPerson
from app.models.team import PlanCode
from utils.mask_person_data import mask_person_data

json_file_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "mocks", "persons.json"
)


def load_data_from_json():
    with open(json_file_path) as json_file:
        data = json.load(json_file)
    return data


def person_total():
    total = load_data_from_json()
    return len(total)


def search_persons(
    db: Session,
    search_condition: Optional[SearchCrossRequest],
    es_client: Elasticsearch,
    page: int,
    per_page: int,
    listing_plan_code: PlanCode,
    current_user: UserBase,
):
    search = ESPersonExtend.search(using=es_client, index=ESPersonExtend.Index.name)
    search_query = build_search_query_by_seach_conditions(
        search_condition=search_condition, current_user=current_user, db=db
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
        "_source": [
            "downloaded_flag",
            "uuid",
            "name",
            "company_name",
            "corporate_number",
            "role_name",
            "address",
            "contactAddress",
            "linkedin_url",
            "twitter_url",
            "fb_url",
            "wantedly_url",
            "github_url",
        ],
    }

    result = search.extra(**pagination_param).execute()["hits"]
    data = result["hits"]._l_
    persons = [x["_source"] for x in data]
    person_uuids = [x["uuid"] for x in persons]

    if listing_plan_code == PlanCode.UNLIMITED:
        for person in persons:
            person["downloaded_flag"] = True
        return persons, 0, 0

    person_uuids_downloaded = (
        db.exec(
            select(TeamPerson.person_uuid)
            .where(TeamPerson.team_id == current_user.team_id)
            .where(col(TeamPerson.person_uuid).in_(person_uuids))
        )
        .scalars()
        .all()
    )

    mark_persons = mask_person_data(persons, person_uuids_downloaded)

    return mark_persons, 0, 0
