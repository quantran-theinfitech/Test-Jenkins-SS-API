from typing import Optional

from sqlalchemy.sql import text
from sqlmodel import Session


def get_exclude_collection_detail(
    db: Session, exclude_collection_id: int, team_id: Optional[int] = None
):
    query = """ SELECT MAX(cec."name") AS name,
              MAX(cec.description) AS description,
              COUNT(DISTINCT ceci.id) AS exclude_collection_count
              FROM company_exclude_collections cec
              LEFT JOIN company_exclude_collection_items ceci
              ON ceci.collection_id = cec.id
              WHERE cec.id = :exclude_collection_id
              and cec.team_id = :team_id """

    company_exclude = db.execute(
        text(query),
        {"exclude_collection_id": exclude_collection_id, "team_id": team_id},
    ).first()

    return company_exclude
