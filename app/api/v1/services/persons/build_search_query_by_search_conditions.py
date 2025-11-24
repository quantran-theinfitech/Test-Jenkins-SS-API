from typing import List

from sqlalchemy import text
from sqlmodel import Session, select

from app.api.v1.queries.person import build_es_query
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.collections.get_corporate_number_by_collection_ids import (
    get_corporate_numbers_by_collection_ids,
)
from app.api.v1.services.enrichments import get_entity_identifier_by_enrichment_id
from app.api.v1.services.person_collections.get_uuid_by_collection_ids import (
    get_uuids_by_collection_ids,
)
from app.models.team import PlanCode, Team


def build_search_query_by_seach_conditions(
    search_condition,
    current_user: UserBase,
    db: Session,
    uuids_csv: List[str] = [],
):
    search_query = []
    uuids_downloaded = []
    corporate_numbers_downloaded = []
    corporate_numbers_by_tags = []
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
        corporate_numbers_by_tags = [
            row[0]
            for row in db.execute(
                text(tag_query),
                {
                    "team_id": current_user.team_id,
                    "tags": "{{{}}}".format(
                        ", ".join(f'"{item}"' for item in set(search_condition.tags))
                    ),
                },
            ).all()
        ]
    if search_condition.is_persons_unlocked and not is_unlimited_account:
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

    if search_condition.is_companies_unlocked and not is_unlimited_account:
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

    search_query = build_es_query(
        search_condition,
        ["".join(uuid_downloaded) for uuid_downloaded in uuids_downloaded],
        uuids_csv,
        [
            "".join(corporate_number_downloaded)
            for corporate_number_downloaded in corporate_numbers_downloaded
        ],
        corporate_numbers_by_tags,
        is_unlimited_account,
    )
    return search_query
