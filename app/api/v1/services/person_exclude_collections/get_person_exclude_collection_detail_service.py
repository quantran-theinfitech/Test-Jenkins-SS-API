from typing import Optional

from sqlalchemy.sql import text
from sqlmodel import Session


def get_person_exclude_collection_detail(
    db: Session, exclude_collection_id: int, team_id: Optional[int] = None
):
    query = """ SELECT MAX(pec."name") AS name,
              MAX(pec.description) AS description,
              COUNT(DISTINCT peci.id) AS exclude_collection_count
              FROM person_exclude_collections pec
              LEFT JOIN person_exclude_collection_items peci
              ON peci.collection_id = pec.id
              WHERE pec.id = :exclude_collection_id
              and pec.team_id = :team_id """

    person_exclude = db.execute(
        text(query),
        {"exclude_collection_id": exclude_collection_id, "team_id": team_id},
    ).first()

    return person_exclude
