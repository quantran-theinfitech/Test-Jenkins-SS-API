from typing import Optional

from sqlalchemy.sql import text
from sqlmodel import Session


def listing_person_exclude_collection_persons(
    exclude_id: int,
    team_id: Optional[int],
    keyword: Optional[str],
    db: Session,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
):
    keyword_query = ""
    if keyword:
        keyword_query = """AND p.name ILIKE :keyword"""
    query = f""" SELECT p.*, MAX(pec.team_id) AS team_id
                FROM person_exclude_collection_items peci
                LEFT JOIN person_exclude_collections pec
                ON pec.id = peci.collection_id
                LEFT JOIN persons p
                ON p.uuid = peci.person_uuid
                WHERE pec.id = :exclude_id AND pec.team_id = :team_id
                {keyword_query}
                GROUP BY p.id
                LIMIT :limit OFFSET :offset """

    offset = 0
    if page is not None and per_page is not None:
        offset = (page - 1) * per_page

    persons = db.execute(
        text(query),
        {
            "exclude_id": exclude_id,
            "team_id": team_id,
            "limit": per_page,
            "offset": offset,
            "keyword": f"%{keyword}%",
        },
    ).all()
    return persons


def get_person_exclude_collection_persons_count(
    db: Session,
    exclude_id: int,
    team_id: Optional[int] = None,
    keyword: Optional[str] = None,
):
    join_persons_query = ""
    keyword_query = ""
    if keyword:
        join_persons_query = """LEFT JOIN persons p ON p.uuid = peci.person_uuid"""
        keyword_query = """AND p.name ILIKE :keyword"""
    count_query = f"""SELECT COUNT(*) FROM
                    person_exclude_collection_items peci
                    LEFT JOIN person_exclude_collections pec
                    ON peci.collection_id = pec.id
                    {join_persons_query}
                    WHERE pec.id = :exclude_id AND pec.team_id = :team_id
                    {keyword_query}
                    """
    total = (
        db.execute(
            text(count_query),
            {"exclude_id": exclude_id, "team_id": team_id, "keyword": f"%{keyword}%"},
        ).scalar()
        or 0
    )
    return total
