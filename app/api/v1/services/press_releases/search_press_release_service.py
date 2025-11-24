from typing import Optional

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from sqlalchemy import text
from sqlmodel import Session, select

from app.api.v1.queries.press_release import build_es_query
from app.api.v1.schemas.elasticsearch.press_releases import ESPressRelease
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.collections.get_corporate_number_by_collection_ids import (
    get_corporate_numbers_by_collection_ids,
)
from app.api.v1.services.enrichments import get_entity_identifier_by_enrichment_id
from app.models.press_release_business_categories import PressReleaseBusinessCategory
from app.models.team import PlanCode
from app.models.team_company import TeamCompany
from utils.hash_id import hash_id


def make_offset_press_release_data(press_releases, corporate_numbers_downloaded: list):
    press_releases_data = []
    for data in press_releases:
        data["contact_email"] = data.get("contact_email")
        data["hp_url"] = data.get("hp_url")
        data["contact_form_url"] = data.get("contact_form_url")
        data["id"] = hash_id(data.get("id", None))
        companies_data = data.get("companies", [])
        if (
            isinstance(companies_data, list)
            and len(companies_data) > 0
            and isinstance(companies_data[0], dict)
        ):
            data.update(companies_data[0])
            data["company_name"] = companies_data[0].get("name", "")
        else:
            data["company_name"] = ""
        if data.get("corporate_number", "") in corporate_numbers_downloaded:
            data["company_downloaded_flag"] = True
        else:
            data["company_downloaded_flag"] = False
        press_releases_data.append(data)

    return press_releases_data


def search_press_releases(
    db: Session,
    search_condition: Optional[SearchCrossRequest],
    es_client: Elasticsearch,
    page: int,
    per_page: int,
    listing_plan_code: PlanCode,
    current_user: UserBase,
):
    search = ESPressRelease.search(using=es_client, index=ESPressRelease.Index.name)
    search_query = build_search_press_release_query(search_condition, current_user, db)
    search: Search = search.query(search_query)
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
    recruits = [x["_source"] for x in data]

    corporate_numbers_downloaded = db.exec(
        select(TeamCompany.corporate_number).where(
            TeamCompany.team_id == current_user.team_id,
        )
    ).all()

    return (
        make_offset_press_release_data(recruits, corporate_numbers_downloaded),
        total,
        unlimited_total,
    )


def build_search_press_release_query(
    search_condition: SearchCrossRequest, current_user: UserBase, db: Session
):
    corporate_numbers_downloaded = []
    if search_condition.is_companies_unlocked:
        corporate_numbers_downloaded = db.exec(
            select(TeamCompany.corporate_number).where(
                TeamCompany.team_id == current_user.team_id,
            )
        ).all()
    if search_condition.company_collections:
        search_condition.corporate_numbers_by_collection = (
            get_corporate_numbers_by_collection_ids(
                db, search_condition.company_collections, current_user
            )
        )
    if search_condition.companies_identified:
        search_condition.corporate_numbers_identified = (
            get_entity_identifier_by_enrichment_id(
                db, current_user, search_condition.companies_identified.enrichment_ids
            )
        )
    corporate_numbers_by_tags = []
    if search_condition.tags:
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

    categories = []
    if search_condition.new_press_release:
        if search_condition.new_press_release.business_categories:
            categories = db.exec(
                select(PressReleaseBusinessCategory.name).where(
                    PressReleaseBusinessCategory.id.in_(
                        search_condition.new_press_release.business_categories
                    )
                )
            ).all()

    search_query = build_es_query(
        search_condition,
        [
            "".join(corporate_number_downloaded)
            for corporate_number_downloaded in corporate_numbers_downloaded
        ],
        ["".join(corporate_number) for corporate_number in corporate_numbers_by_tags],
        categories,
    )
    return search_query
