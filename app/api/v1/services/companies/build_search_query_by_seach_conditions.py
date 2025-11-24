from typing import List

from sqlalchemy import text
from sqlmodel import Session, select

from app.api.v1.queries.company import build_es_query
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.collections.get_corporate_number_by_collection_ids import (
    get_corporate_numbers_by_collection_ids,
)
from app.api.v1.services.enrichments import get_entity_identifier_by_enrichment_id
from app.api.v1.services.person_collections.get_uuid_by_collection_ids import (
    get_uuids_by_collection_ids,
)
from app.models.press_release_business_categories import PressReleaseBusinessCategory
from app.models.team import PlanCode, Team


def build_search_query_by_seach_conditions(
    search_condition,
    current_user: UserBase,
    db: Session,
    corporate_numbers_csv: List[str] = [],
):
    search_query = []
    corporate_numbers_by_tags = []
    corporate_numbers_downloaded = []
    uuids_downloaded = []
    listing_plan_code = db.exec(
        select(Team.listing_plan_code).where(Team.id == current_user.team_id)
    ).first()
    is_unlimited_account = listing_plan_code == PlanCode.UNLIMITED
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
    if search_condition.is_companies_unlocked:
        companies_downloaded_query = """
            SELECT tc.corporate_number
            FROM team_companies tc
            LEFT JOIN companies c ON tc.corporate_number = c.corporate_number
            WHERE tc.team_id = :team_id"""

        corporate_numbers_downloaded = db.execute(
            text(companies_downloaded_query),
            {
                "team_id": current_user.team_id,
            },
        ).all()

    if search_condition.is_persons_unlocked:
        query = """
            SELECT tp.person_uuid FROM team_persons tp
            LEFT JOIN persons p
            ON tp.person_uuid = p.uuid
            WHERE tp.team_id = :team_id
            """

        uuids_downloaded = db.execute(
            text(query),
            {
                "team_id": current_user.team_id,
            },
        ).all()

    if search_condition.company_collections:
        search_condition.corporate_numbers_by_collection = (
            get_corporate_numbers_by_collection_ids(
                db, search_condition.company_collections, current_user
            )
        )
    if search_condition.person_collections:
        search_condition.uuids_by_collection = get_uuids_by_collection_ids(
            db, search_condition.person_collections, current_user
        )

    if search_condition.companies_identified:
        search_condition.corporate_numbers_identified = (
            get_entity_identifier_by_enrichment_id(
                db, current_user, search_condition.companies_identified.enrichment_ids
            )
        )

    new_press_release_categrories = []
    if search_condition.new_press_release:
        if search_condition.new_press_release.business_categories:
            new_press_release_categrories = db.exec(
                select(PressReleaseBusinessCategory.name).where(
                    PressReleaseBusinessCategory.id.in_(
                        search_condition.new_press_release.business_categories
                    )
                )
            ).all()

    search_query = build_es_query(
        search_condition,
        ["".join(corporate_number) for corporate_number in corporate_numbers_by_tags],
        [
            "".join(corporate_number_downloaded)
            for corporate_number_downloaded in corporate_numbers_downloaded
        ],
        corporate_numbers_csv,
        ["".join(uuid_downloaded) for uuid_downloaded in uuids_downloaded],
        new_press_release_categrories,
        is_unlimited_account,
    )
    return search_query
