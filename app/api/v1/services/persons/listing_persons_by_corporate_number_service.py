# flake8: noqa: E501
from typing import List

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Search
from sqlalchemy import select
from sqlalchemy.sql import text
from sqlmodel import Session, col

from app.api.v1.schemas.elasticsearch.persons_extend import ESPersonExtend
from app.api.v1.schemas.persons import RoleGroupCode, RoleGroupCodeResponse
from app.api.v1.schemas.users import UserBase
from app.models import TeamPerson
from app.models.team import PlanCode
from utils.mask_person_data import mask_person_sql_data


def handle_role_group_codes(role_group_code) -> str:
    if not isinstance(role_group_code, str):
        return str(role_group_code) if role_group_code else ""

    mapping = {
        "役員クラス": RoleGroupCodeResponse.CXO,
        "社長": RoleGroupCodeResponse.CXO,
        "責任者クラス": RoleGroupCodeResponse.Director,
    }
    return mapping.get(role_group_code, RoleGroupCodeResponse.Other).value


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


def add_optout_query(search_query):
    return Q(
        "bool",
        must=[search_query, Q("bool", must_not=[Q("exists", field="is_opt_out")])],
    )


def listing_person_by_corporate_number(
    corporate_number: str,
    db: Session,
    es_client: Elasticsearch,
    user: UserBase,
    listing_plan_code: PlanCode,
    page: int,
    per_page: int,
    role_group_code: List[RoleGroupCode],
):
    search = ESPersonExtend.search(using=es_client, index=ESPersonExtend.Index.name)

    role_group_code_map = {
        RoleGroupCode.CXO: ["役員クラス", "社長"],
        RoleGroupCode.Director: ["責任者クラス"],
    }

    search_query = Q("bool", must=[Q("terms", corporate_number=[corporate_number])])

    if role_group_code:
        script_condition = "true"
        if len(role_group_code) == 1:
            role_values = role_group_code_map.get(role_group_code[0], None)

            script_condition = (
                " || ".join(
                    [f'doc["role_group_codes"][i] == "{val}"' for val in role_values]
                )
                if role_values
                else 'doc["role_group_codes"][i] != "責任者クラス" && doc["role_group_codes"][i] != "役員クラス" && doc["role_group_codes"][i] != "社長"'
            )

        if (
            len(role_group_code) == 2
            and RoleGroupCode.CXO in role_group_code
            and RoleGroupCode.Director in role_group_code
        ):
            script_condition = 'doc["role_group_codes"][i] == "役員クラス" || doc["role_group_codes"][i] == "社長" || doc["role_group_codes"][i] == "責任者クラス"'

        search_query = Q(
            "bool",
            must=[
                Q("terms", corporate_number=[corporate_number]),
                Q(
                    "script",
                    script={
                        "source": f"""
                            if (!doc.containsKey('corporate_number') || !doc.containsKey('role_group_codes') || doc['corporate_number'].size() == 0 || doc['role_group_codes'].size() == 0) return false;
                            for (int i = 0; i < doc['corporate_number'].length; i++) {{
                                if ((doc['corporate_number'][i] == params.cn) && ({script_condition})) {{
                                    return true;
                                }}
                            }}
                            return false;
                        """,
                        "params": {"cn": corporate_number},
                    },
                ),
            ],
        )

    search_query = add_ranking_query(search_query)
    search_query = add_optout_query(search_query)
    search: Search = search.query(search_query)
    search = search.sort("_score", "_id")
    search = search.params(request_timeout=30)

    if (10000 - ((page - 1) * per_page)) < 15:
        size = 10000 - ((page - 1) * per_page)
    else:
        size = per_page

    pagination_param = {
        "size": size,
        "from": (page - 1) * per_page,
        "track_total_hits": True,
        "_source": [
            "downloaded_flag",
            "uuid",
            "name",
            "company_name",
            "role_name",
            "role_group_codes",
            "corporate_number",
            "address",
            "linkedin_url",
            "twitter_url",
            "fb_url",
            "wantedly_url",
            "github_url",
        ],
    }

    result = search.extra(**pagination_param).execute()["hits"]
    data = result["hits"]._l_
    unlimited_total = result._d_["total"]["value"]
    total = unlimited_total if unlimited_total <= 10000 else 10000
    persons = [x["_source"] for x in data]

    for person in persons:
        if corporate_number in person["corporate_number"]:
            corporate_number_index = person["corporate_number"].index(corporate_number)

            if len(person["company_name"]) > corporate_number_index:
                person["company_name"] = [
                    person["company_name"][corporate_number_index]
                ]
            if len(person["role_name"]) > corporate_number_index:
                person["role_name"] = [person["role_name"][corporate_number_index]]

            if len(person["role_group_codes"]) > corporate_number_index:
                person["role_group_codes"] = [
                    str(
                        handle_role_group_codes(
                            person["role_group_codes"][corporate_number_index]
                        )
                    )
                ]
            else:
                person["role_group_codes"] = [
                    str(handle_role_group_codes(role))
                    for role in person["role_group_codes"]
                ]

            person["corporate_number"] = [
                person["corporate_number"][corporate_number_index]
            ]

    if listing_plan_code == PlanCode.UNLIMITED:
        mask_persons = []
        for person in persons:
            mask_person = dict(person)
            mask_person["downloaded_flag"] = True
            mask_persons.append(mask_person)
        return mask_persons, total
    person_uuids = [x["uuid"] for x in persons]
    person_uuids_downloaded = (
        db.exec(
            select(TeamPerson.person_uuid)
            .where(TeamPerson.team_id == user.team_id)
            .where(col(TeamPerson.person_uuid).in_(person_uuids))
        )
        .scalars()
        .all()
    )
    mask_persons = mask_person_sql_data(persons, person_uuids_downloaded)
    return mask_persons, total
