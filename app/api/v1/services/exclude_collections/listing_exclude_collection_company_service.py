from typing import Optional

from sqlalchemy.sql import text
from sqlmodel import Session


def listing_exclude_collection_companies(
    exclude_id: int,
    team_id: Optional[int],
    keyword: Optional[str],
    db: Session,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
):
    keyword_query = ""
    if keyword:
        keyword_query = """AND c.name ILIKE :keyword"""
    query = f""" SELECT c.*, MAX(cec.team_id) AS team_id,
                MAX(tc.tags) AS tags
                FROM company_exclude_collection_items ceci
                LEFT JOIN company_exclude_collections cec
                ON cec.id = ceci.collection_id
                LEFT JOIN companies c
                ON c.corporate_number = ceci.corporate_number
                LEFT JOIN team_companies tc ON
                tc.corporate_number = c.corporate_number
                WHERE cec.id = :exclude_id AND cec.team_id = :team_id
                {keyword_query}
                GROUP BY c.id
                LIMIT :limit OFFSET :offset """

    offset = 0
    if page is not None and per_page is not None:
        offset = (page - 1) * per_page

    companies = db.execute(
        text(query),
        {
            "exclude_id": exclude_id,
            "team_id": team_id,
            "limit": per_page,
            "offset": offset,
            "keyword": f"%{keyword}%",
        },
    ).all()
    return companies


def get_exclude_collection_companies_count(
    db: Session,
    exclude_id: int,
    team_id: Optional[int] = None,
    keyword: Optional[str] = None,
):
    join_companies_query = ""
    keyword_query = ""
    if keyword:
        join_companies_query = (
            """LEFT JOIN companies c ON c.corporate_number = ceci.corporate_number"""
        )
        keyword_query = """AND c.name ILIKE :keyword"""
    count_query = f""" SELECT COUNT(*)
                    FROM company_exclude_collection_items ceci
                    LEFT JOIN company_exclude_collections cec
                    ON ceci.collection_id = cec.id
                    {join_companies_query}
                    WHERE cec.id = :exclude_id AND cec.team_id = :team_id
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
