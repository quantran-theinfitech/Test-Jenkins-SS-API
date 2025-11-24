from typing import Optional

from fastapi import Query
from sqlalchemy import distinct, func
from sqlalchemy.sql import text
from sqlalchemy.sql.operators import is_
from sqlmodel import Session, col, select

from app.api.v1.schemas.users import UserBase
from app.models.company_collection import CompanyCollection, StatusCode, TypeCode
from app.models.company_collection_tags import CompanyCollectionTag


def get_all_collections_count(
    db: Session,
    user: UserBase,
    status_code: Optional[StatusCode] = None,
    keyword: Optional[str] = Query(default=None),
    group_id: Optional[int] = None,
    type_code: Optional[str] = None,
):
    # total
    total_query = (
        select(CompanyCollection)
        .join(
            CompanyCollectionTag,
            CompanyCollectionTag.collection_id == CompanyCollection.id,
            isouter=True,
        )
        .where(CompanyCollection.team_id == user.team_id)
        .where(is_(CompanyCollection.deleted_at, None))
    )
    if group_id:
        total_query = total_query.where(CompanyCollection.group_id == group_id)
    if status_code:
        total_query = total_query.where(CompanyCollection.status_code == status_code)
    if type_code == TypeCode.CSV:
        total_query = total_query.where(CompanyCollection.type_code == type_code)
    elif type_code == TypeCode.SYS:
        total_query = total_query.where(CompanyCollection.type_code.is_(None))
    if keyword:
        total_query = total_query.where(
            col(CompanyCollection.name).ilike(f"%{keyword}%")
            | col(CompanyCollectionTag.name).ilike(f"%{keyword}%")
        )
    total = (
        db.execute(
            total_query.with_only_columns(func.count(distinct(CompanyCollection.id)))
        ).scalar()
        or 0
    )
    return total


def get_all_collections(
    db: Session,
    user: UserBase,
    status_code: Optional[StatusCode] = None,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
    keyword: Optional[str] = None,
    group_id: Optional[int] = None,
    type_code: Optional[str] = None,
):
    query_params = {
        "team_id": user.team_id,
    }

    search_condition = ""
    if keyword:
        search_condition = """AND (cc.name ILIKE :keyword OR cct.name ILIKE :keyword)"""
        query_params["keyword"] = f"%{keyword}%"

    listing_collection_by_group_id = ""
    if group_id:
        listing_collection_by_group_id = """AND cc.group_id = :group_id"""
        query_params["group_id"] = group_id

    status_condition = ""
    if status_code is not None:
        status_condition = "AND cc.status_code = :status_code"
        query_params["status_code"] = status_code

    type_code_condition = ""
    if type_code == TypeCode.CSV:
        type_code_condition = "AND cc.type_code = :type_code"
        query_params["type_code"] = type_code
    elif type_code == TypeCode.SYS:
        type_code_condition = "AND cc.type_code IS NULL"

    query = f"""SELECT
            cc.id,
            cc.name,
            cc.description,
            cc.status_code,
            cc.type_code,
            (
                COUNT(DISTINCT cci.corporate_number) +
                COUNT(DISTINCT cci.company_custom_id)
            ) AS companies_count,
            ARRAY_AGG(DISTINCT u.name ORDER BY u.name)
                FILTER (WHERE u.name IS NOT NULL) AS assignees,
            ARRAY_AGG(DISTINCT cct.name ORDER BY cct.name)
                FILTER (WHERE cct.name IS NOT NULL) AS tags,
            cc.created_at
        FROM company_collections cc
            LEFT JOIN
            company_collection_items cci ON cc.id = cci.collection_id
            LEFT JOIN company_collection_assignees cca ON cc.id = cca.collection_id
            LEFT JOIN users u ON cca.user_id = u.id AND u.deleted_at IS NULL
            LEFT JOIN company_collection_tags cct ON cc.id = cct.collection_id
        WHERE cc.team_id = :team_id AND cc.deleted_at IS NULL
        {search_condition}
        {listing_collection_by_group_id}
        {status_condition}
        {type_code_condition}
        GROUP BY cc.id
        ORDER BY cc.created_at DESC, cc.id DESC
    """

    if per_page is not None and page is not None:
        query += " LIMIT :per_page OFFSET :offset"
        query_params["per_page"] = per_page
        query_params["offset"] = (page - 1) * per_page

    collections = db.execute(text(query), query_params).all()
    return collections
