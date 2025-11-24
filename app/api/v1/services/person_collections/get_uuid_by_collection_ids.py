from typing import Optional

from sqlalchemy import text
from sqlmodel import Session

from app.api.v1.schemas.search_cross import CollectionList, UuidsByCollection
from app.api.v1.schemas.users import UserBase


def get_uuids_by_collection_ids(
    db: Session,
    person_collections: Optional[CollectionList],
    current_user: UserBase,
):
    def fetch_uuids(collection_ids, team_id):
        query = text(
            """
            SELECT DISTINCT pci.person_uuid
            FROM person_collection_items pci
            LEFT JOIN person_collections pc ON pci.collection_id = pc.id
            WHERE pci.collection_id = ANY(:collection_ids)
            AND pc.team_id = :team_id
            AND pc.deleted_at IS NULL
            """
        )
        results = db.execute(
            query,
            {
                "team_id": team_id,
                "collection_ids": collection_ids,
            },
        ).fetchall()
        return [row.person_uuid for row in results]

    or_person_uuids = []
    exclude_person_uuids = []

    if person_collections.or_collections:
        or_person_uuids = fetch_uuids(
            person_collections.or_collections,
            current_user.team_id,
        )

    if person_collections.exclude_collections:
        exclude_person_uuids = fetch_uuids(
            person_collections.exclude_collections,
            current_user.team_id,
        )

    return UuidsByCollection(
        or_uuids=or_person_uuids,
        exclude_uuids=exclude_person_uuids,
    )
