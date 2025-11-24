from typing import Optional

from sqlalchemy.sql import text
from sqlmodel import Session

from app.api.v1.schemas.users import UserBase
from app.models.person_collection import StatusCode, TypeCode


def listing_person_collections(
    db: Session,
    page: int,
    per_page: int,
    user: UserBase,
    keyword: Optional[str] = None,
    status_code: Optional[StatusCode] = StatusCode.Open,
    group_id: Optional[int] = None,
    type_code: Optional[TypeCode] = None,
):
    query_params = {
        "team_id": user.team_id,
    }

    conditions = ["pc.team_id = :team_id", "pc.deleted_at IS NULL"]

    if keyword:
        conditions.append("pc.name ILIKE :keyword")
        query_params["keyword"] = f"%{keyword}%"

    if group_id is not None:
        conditions.append("pc.group_id = :group_id")
        query_params["group_id"] = group_id

    if status_code is not None:
        conditions.append("pc.status_code = :status_code")
        query_params["status_code"] = status_code

    if type_code is not None:
        conditions.append("pc.type_code = :type_code")
        query_params["type_code"] = type_code

    where_clause = " AND ".join(conditions)

    query = f"""
        SELECT pc.id,
               pc.name,
               pc.description,
               pc.tags,
               pc.created_at,
               pc.type_code,
               pc.status_code,
               COUNT(DISTINCT pci.person_uuid) AS person_count,
               ARRAY_AGG(u.name) FILTER (WHERE u.name IS NOT NULL) AS assignees
        FROM person_collections AS pc
        LEFT JOIN person_collection_items AS pci ON pci.collection_id = pc.id
        LEFT JOIN person_collection_assignees AS pca ON pca.collection_id = pc.id
        LEFT JOIN users AS u ON u.id = pca.assignee_id AND u.deleted_at IS NULL
        WHERE {where_clause}
        GROUP BY pc.id
        ORDER BY pc.created_at DESC, pc.id DESC
    """

    if per_page and page:
        query += " LIMIT :limit OFFSET :offset"
        query_params.update({"limit": per_page, "offset": (page - 1) * per_page})

    return db.execute(text(query), query_params).all()


def count_person_collections(
    db: Session,
    user: UserBase,
    keyword: Optional[str] = None,
    status_code: Optional[StatusCode] = StatusCode.Open,
    group_id: Optional[int] = None,
    type_code: Optional[TypeCode] = None,
):
    keyword_query = ""
    group_id_query = ""
    status_code_query = ""
    type_code_query = ""

    query_params = {
        "team_id": user.team_id,
        "keyword": f"%{keyword}%",
        "group_id": group_id,
    }

    if keyword is not None:
        keyword_query = """AND (pc.name ILIKE :keyword)"""
    if group_id is not None:
        group_id_query = """AND (pc.group_id = :group_id)"""
    if status_code is not None:
        status_code_query = """AND (pc.status_code = :status_code)"""
        query_params["status_code"] = status_code
    if type_code is not None:
        type_code_query = """AND (pc.type_code = :type_code)"""
        query_params["type_code"] = type_code

    count_query = f"""SELECT COUNT(pc.id)
                    FROM person_collections AS pc
                    WHERE pc.team_id = :team_id AND pc.deleted_at IS NULL
                    {keyword_query}
                    {group_id_query}
                    {status_code_query}
                    {type_code_query}
                    """
    total = db.execute(text(count_query), query_params).scalar() or 0
    return total
