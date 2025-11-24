from typing import List, Optional

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q
from sqlmodel import Session, func, select

from app.api.v1.schemas.elasticsearch.persons_extend import ESPersonExtend
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.persons.build_search_query_by_search_conditions import (
    build_search_query_by_seach_conditions,
)
from app.models.team import PlanCode
from app.models.team_person import TeamPerson



def get_total_lock_unlock_person_service(
    db: Session,
    uuids: List,
    listing_plan_code: PlanCode,
    current_user: UserBase,
):
    total = len(uuids)

    if listing_plan_code == PlanCode.UNLIMITED:
        return {
            "total": total,
            "total_lock": 0,
            "total_unlock": total,
        }

    result = db.exec(
        select(func.count(func.distinct(TeamPerson.person_uuid)).label("total_unlock"))
        .where(TeamPerson.team_id == current_user.team_id)
        .where(TeamPerson.person_uuid.in_(uuids))
    ).first()

    total_unlock = result if result else 0
    return {
        "total": total,
        "total_lock": total - total_unlock,
        "total_unlock": total_unlock,
    }

def listing_person_uuids_by_select(
    db: Session,
    search_condition: Optional[SearchCrossRequest],
    es_client: Elasticsearch,
    page: int,
    per_page: int,
    current_user: UserBase,
    max_person_by_company: int,
):
    search = ESPersonExtend.search(using=es_client, index=ESPersonExtend.Index.name)
    search_query = build_search_query_by_seach_conditions(
        search_condition, current_user, db
    )
    search_query = add_ranking_query(search_query)
    search = search.query(search_query).sort("_score", "_id")
    search = search.params(request_timeout=30)
    if search_condition and search_condition.is_default_filter:
        search = search.params(request_cache=True)

    corporate_numbers_obj = {}
    added_persons = set()
    list_person = []

    while True:
        size = calculate_size(page, per_page)
        if size != per_page:
            return added_persons
        pagination_param = {
            "size": size,
            "from": (page - 1) * per_page,
            "track_total_hits": False,
            "_source": [
                "uuid",
                "corporate_number",
            ],
        }

        result = search.extra(**pagination_param).execute()["hits"]
        data = result["hits"]._l_
        if len(data) == 0:
            return added_persons

        page += 1
        persons = [x["_source"] for x in data]

        list_uuids = []
        for person in persons:
            list_uuids.append(person.get("uuid"))
            person["downloaded_flag"] = True

        if max_person_by_company > 0:
            process_persons(
                persons,
                corporate_numbers_obj,
                added_persons,
                list_person,
                max_person_by_company,
                per_page,
            )
            if len(added_persons) == per_page:
                return added_persons
        else:
            break

    return list_uuids


def add_ranking_query(search_query):
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

    return Q("bool", must=search_query, should=ranking_query, minimum_should_match=0)


def calculate_size(page, per_page):
    if (10000 - (page * per_page)) < 0:
        return 10000 - ((page - 1) * per_page)
    else:
        return per_page


def process_persons(
    persons,
    corporate_numbers_obj,
    added_persons,
    list_person,
    max_person_by_company,
    per_page,
):
    for person in persons:
        corporate_numbers = person["corporate_number"]
        person_key = person["uuid"]

        if should_add_person(corporate_numbers, person_key, added_persons):
            add_person(person, list_person, added_persons)
        else:
            process_corporate_numbers(
                corporate_numbers,
                corporate_numbers_obj,
                person_key,
                max_person_by_company,
                person,
                list_person,
                added_persons,
            )

        if len(added_persons) == per_page:
            break


def should_add_person(corporate_numbers, person_key, added_persons):
    return all(not cn for cn in corporate_numbers) and person_key not in added_persons


def add_person(person, list_person, added_persons):
    list_person.append(person)
    added_persons.add(person["uuid"])


def process_corporate_numbers(
    corporate_numbers,
    corporate_numbers_obj,
    person_key,
    max_person_by_company,
    person,
    list_person,
    added_persons,
):
    for cn in corporate_numbers:
        if not cn:
            continue

        count = corporate_numbers_obj.setdefault(cn, 0)
        if count < max_person_by_company and person_key not in added_persons:
            corporate_numbers_obj[cn] += 1
            add_person(person, list_person, added_persons)
