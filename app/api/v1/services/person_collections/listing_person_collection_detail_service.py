from typing import Literal, Optional

from sqlalchemy.sql import text
from sqlmodel import Session

from app.models.person import Person


def get_collection_persons(
    collection_id: int,
    team_id: Optional[int],
    db: Session,
    page: int,
    per_page: int,
    keyword: Optional[str] = None,
    order_by: Optional[Literal[tuple(Person.__fields__.keys())]] = "id",
    order_by_desc_flag: Optional[bool] = False,
):
    keywordQuery = ""
    order_by_query = "ORDER BY p.uuid"
    order_type_query = "ASC"
    query_params = {
        "collection_id": collection_id,
        "team_id": team_id,
        "keyword": f"%{keyword}%",
        "limit": per_page,
        "offset": (page - 1) * per_page,
        "order_by": order_by,
    }

    if keyword:
        keywordQuery = """AND (
            p.name ILIKE :keyword OR
            array_to_string(p.role_name, ', ') ILIKE :keyword OR
            array_to_string(p.company_name, ', ') ILIKE :keyword
        )"""
    if order_by:
        order_by_query = f"ORDER BY p.{order_by}"
    if order_by_desc_flag:
        order_type_query = "DESC"

    query = f"""SELECT p.*, MAX(pc.tags) AS tags,
                MAX(pc.status_code) AS status_code
                FROM person_collection_items pci
                LEFT JOIN persons p
                ON p.uuid = pci.person_uuid
                LEFT JOIN person_collections pc
                ON pc.id = pci.collection_id
                WHERE pc.id = :collection_id
                AND pc.team_id = :team_id
                {keywordQuery}
                GROUP BY p.id
                {order_by_query}
                {order_type_query}
                LIMIT :limit OFFSET :offset
                """
    listing_collection_detail = db.execute(text(query), query_params).all()
    return listing_collection_detail


def count_get_collection_persons(
    collection_id: int,
    team_id: Optional[int],
    db: Session,
    keyword: Optional[str] = None,
):
    keywordQuery = ""
    query_params = {
        "collection_id": collection_id,
        "team_id": team_id,
        "keyword": f"%{keyword}%",
    }

    if keyword:
        keywordQuery = """AND (
            p.name ILIKE :keyword OR
            array_to_string(p.role_name, ', ') ILIKE :keyword OR
            array_to_string(p.company_name, ', ') ILIKE :keyword
        )"""

    count_query = f"""SELECT count(*) FROM persons p
                LEFT JOIN person_collection_items pci
                ON pci.person_uuid = p.uuid
                LEFT JOIN person_collections pc
                ON pc.id = pci.collection_id
                WHERE pci.collection_id = :collection_id
                AND pc.team_id = :team_id
                {keywordQuery}
                """
    total = db.execute(text(count_query), query_params).scalar() or 0
    return total
