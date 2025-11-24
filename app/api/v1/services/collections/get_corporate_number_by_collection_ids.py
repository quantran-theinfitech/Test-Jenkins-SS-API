from typing import Optional

from sqlalchemy import text
from sqlmodel import Session

from app.api.v1.schemas.search_cross import CollectionList, CorporateNumberByCollection
from app.api.v1.schemas.users import UserBase


def get_corporate_numbers_by_collection_ids(
    db: Session,
    company_collections: Optional[CollectionList],
    current_user: UserBase,
):
    def fetch_corporate_numbers_by_company(collection_ids, team_id):
        query = text(
            """
            SELECT DISTINCT cci.corporate_number
            FROM company_collection_items cci
            LEFT JOIN company_collections cc ON cci.collection_id = cc.id
            WHERE cci.collection_id = ANY(:collection_ids)
            AND cc.team_id = :team_id
            AND cc.deleted_at IS NULL
            """
        )
        results = db.execute(
            query,
            {
                "team_id": team_id,
                "collection_ids": collection_ids,
            },
        ).fetchall()
        return [row.corporate_number for row in results]

    or_corporate_numbers = []
    exclude_corporate_numbers = []

    if company_collections.or_collections:
        or_corporate_numbers = fetch_corporate_numbers_by_company(
            company_collections.or_collections,
            current_user.team_id,
        )

    if company_collections.exclude_collections:
        exclude_corporate_numbers = fetch_corporate_numbers_by_company(
            company_collections.exclude_collections,
            current_user.team_id,
        )
    return CorporateNumberByCollection(
        or_corporate_numbers=or_corporate_numbers,
        exclude_corporate_numbers=exclude_corporate_numbers,
    )
