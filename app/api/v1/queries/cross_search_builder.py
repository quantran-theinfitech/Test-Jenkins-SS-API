from typing import List

from elasticsearch_dsl import Q
from sqlmodel import Session, select

from app.api.v1.queries.cross import (
    _filter_by_posted_at_es_query,
    build_person_es_query,
    build_press_release_es_query,
)
from app.api.v1.schemas.search_cross import (
    SearchCrossRequest,
    SearchMode,
    SearchPersonRequest,
)
from app.api.v1.schemas.search_press_releases import SearchPressReleaseRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.person_collections.get_uuid_by_collection_ids import (
    get_uuids_by_collection_ids,
)
from app.models.press_release_business_categories import PressReleaseBusinessCategory
from app.models.team_person import TeamPerson


def build_recruit_two_step_query(
    db: Session,
    request: SearchCrossRequest,
    corporate_numbers: List[str],
    query_by_corporate_number: bool,
    current_user: UserBase,
):
    from app.api.v1.queries.recruit import build_es_query

    if query_by_corporate_number:
        return Q(
            "bool",
            must=[
                Q("terms", corporate_number=corporate_numbers),
                build_es_query(request, db, current_user),
            ],
        )
    else:
        return build_es_query(request, db, current_user)


def build_press_release_two_step_query(
    db: Session, request: SearchCrossRequest, corporate_numbers: List[str]
):
    business_categories = []
    match_companies_query = Q("terms", companies__corporate_number=corporate_numbers)

    if request.new_press_release:
        business_categories = _get_press_release_business_categories(
            db, request.new_press_release
        )
        press_release_query = build_press_release_es_query(
            request.new_press_release, is_nested=False, categories=business_categories
        )

        queries = [
            Q("bool", must=press_release_query),
            match_companies_query,
            _filter_by_posted_at_es_query(False),
        ]
    else:
        queries = [match_companies_query, _filter_by_posted_at_es_query(False)]

    return Q("bool", must=queries)


def _get_press_release_business_categories(
    db: Session, request: SearchPressReleaseRequest
):
    business_categories = []
    if request.business_categories:
        business_categories = db.exec(
            select(PressReleaseBusinessCategory.name).where(
                PressReleaseBusinessCategory.id.in_(request.business_categories)
            )
        ).all()
    return business_categories


def build_person_two_step_query(
    db: Session,
    current_user: UserBase,
    request: SearchCrossRequest,
    corporate_numbers: List[str],
):
    queries = []
    uuids_downloaded = _get_downloaded_person_uuids(db, current_user, request)

    person_queries = build_person_es_query(
        request,
        is_nested=False,
        persons_uuids=[
            "".join(uuid_downloaded) for uuid_downloaded in uuids_downloaded
        ],
        persons_csv_uuids=request.uuids_by_collection,
    )
    corporate_numbers_query = [
        Q(
            "nested",
            path="companies",
            query=Q("terms", companies__corporate_number=corporate_numbers),
        )
    ]
    if request.mode == SearchMode.FUZZY:
        corporate_numbers_query.append(
            Q(
                "nested",
                path="companies_fuzzy",
                query=Q("terms", companies_fuzzy__corporate_number=corporate_numbers),
            )
        )

    queries = [
        Q("bool", must=person_queries),
        Q("bool", should=corporate_numbers_query),
    ]
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

    return Q("bool", must=queries, should=ranking_query, minimum_should_match=0)


def _get_downloaded_person_uuids(
    db: Session, current_user: UserBase, request: SearchPersonRequest
):
    uuids_downloaded = []
    if request.is_persons_unlocked:
        uuids_downloaded = db.exec(
            select(TeamPerson.person_uuid).where(
                TeamPerson.team_id == current_user.team_id
            )
        ).all()

    if request.person_collections:
        request.uuids_by_collection = get_uuids_by_collection_ids(
            db, request.person_collections, current_user
        )
    return uuids_downloaded
