from typing import Optional

import sqlalchemy
from fastapi import Query
from sqlalchemy import distinct, func
from sqlalchemy.sql import text
from sqlalchemy.sql.operators import is_
from sqlmodel import Session, col, select

from app.api.v1.schemas.groups import CreateGroupRequest, GroupBase
from app.api.v1.schemas.users import UserBase
from app.models.company_collection import CompanyCollection, StatusCode
from app.models.company_collection_tags import CompanyCollectionTag
from app.models.group import Group
from app.models.person_collection import PersonCollection


class GroupService:
    def __init__(self, db: Session):
        self.db = db

    def create_group(self, request: CreateGroupRequest, current_user: UserBase):
        new_group = Group(
            team_id=current_user.team_id,
            name=request.name,
            description=request.description,
        )
        self.db.add(new_group)
        self.db.commit()
        return new_group.id

    def get_group_detail(self, id: int, user: UserBase) -> GroupBase:
        # get group detail
        group = (
            self.db.query(Group)
            .where(Group.id == id)
            .where(Group.team_id == user.team_id)
            .one()
        )
        return group

    def count_group_collections(
        self,
        user: UserBase,
        id: int,
        status_code: Optional[StatusCode] = None,
        keyword: Optional[str] = Query(default=None),
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
            .where(CompanyCollection.group_id == id)
        )
        if status_code:
            total_query = total_query.where(
                CompanyCollection.status_code == status_code
            )
        if keyword:
            total_query = total_query.where(
                col(CompanyCollection.name).ilike(f"%{keyword}%")
                | col(CompanyCollectionTag.name).ilike(f"%{keyword}%")
            )
        total = (
            self.db.execute(
                total_query.with_only_columns(
                    func.count(distinct(CompanyCollection.id))
                )
            ).scalar()
            or 0
        )
        return total

    def listing_group_collections(
        self,
        user: UserBase,
        id: int,
        status_code: Optional[StatusCode] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        keyword: Optional[str] = Query(default=None),
    ):
        # keyword
        if keyword:
            search_condition = """
                AND (cc.name ILIKE :keyword
                OR cct.name ILIKE :keyword)
            """
        else:
            search_condition = ""

        # get collections of group
        query = f"""SELECT
            cc.id,
            cc.name,
            cc.status_code,
            cc.description,
            COUNT(DISTINCT cci.corporate_number) AS companies_count,
            ARRAY_AGG(DISTINCT u.name) FILTER (WHERE u.name IS NOT NULL) AS assignees,
            ARRAY_AGG(DISTINCT cct.name) FILTER (WHERE cct.name IS NOT NULL) AS tags,
            cc.created_at
        FROM company_collections cc
            LEFT JOIN
                company_collection_items cci ON cc.id = cci.collection_id
            LEFT JOIN
                company_collection_assignees cca ON cc.id = cca.collection_id
            LEFT JOIN
                users u ON cca.user_id = u.id AND u.deleted_at IS NULL
            LEFT JOIN
                company_collection_tags cct ON cc.id = cct.collection_id
        WHERE
            cc.group_id = :id
        AND
            cc.team_id = :team_id
        {search_condition}"""
        if status_code is not None:
            query += " AND cc.status_code = :status_code"

        query += " GROUP BY cc.id ORDER BY cc.created_at DESC"

        if per_page is not None and page is not None:
            query += " LIMIT :per_page OFFSET :offset"
            offset = (page - 1) * per_page
            collections = self.db.execute(
                text(query),
                {
                    "id": id,
                    "team_id": user.team_id,
                    "keyword": f"%{keyword}%",
                    "status_code": status_code,
                    "per_page": per_page,
                    "offset": offset,
                },
            )
        else:
            collections = self.db.execute(
                text(query),
                {
                    "id": id,
                    "team_id": user.team_id,
                    "keyword": f"%{keyword}%",
                    "status_code": status_code,
                },
            )

        return collections

    def listing_groups(
        self,
        current_user: UserBase,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        keyword: Optional[str] = Query(default=None),
    ):
        query = (
            sqlalchemy.select(
                Group.id,
                Group.team_id,
                Group.name,
                Group.description,
                Group.default_flag,
                func.count(func.DISTINCT(CompanyCollection.id)).label(
                    "company_collection_count"
                ),
                func.count(func.DISTINCT(PersonCollection.id)).label(
                    "person_collection_count"
                ),
                Group.created_at,
                Group.created_by,
                Group.updated_at,
                Group.updated_by,
            )
            .join(
                CompanyCollection, CompanyCollection.group_id == Group.id, isouter=True
            )
            .join(PersonCollection, PersonCollection.group_id == Group.id, isouter=True)
            .where(is_(Group.deleted_at, None))
            .where(Group.team_id == current_user.team_id)
        )
        if keyword:
            query = query.where(col(Group.name).ilike(f"%{keyword}%"))

        total = (
            self.db.execute(
                query.with_only_columns(func.count(distinct(Group.id)))
            ).scalar()
            or 0
        )

        query = query.group_by(Group.id)
        query = query.order_by(
            Group.default_flag.desc().nullslast(),
            func.count(func.DISTINCT(CompanyCollection.id)).desc(),
            func.count(func.DISTINCT(PersonCollection.id)).desc(),
        )
        if page is not None and per_page is not None:
            query = query.offset((page - 1) * per_page)
            query = query.limit(per_page)
        list_group = self.db.execute(query).all()

        return list_group, total

    def listing_person_collections(
        self,
        id,
        current_user: UserBase,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ):
        query = (
            sqlalchemy.select(PersonCollection)
            .where(PersonCollection.team_id == current_user.team_id)
            .where(PersonCollection.group_id == id)
        )

        total = (
            self.db.execute(
                query.with_only_columns(func.count(distinct(PersonCollection.id)))
            ).scalar()
            or 0
        )

        query = query.order_by(col(PersonCollection.id).asc())

        if page is not None and per_page is not None:
            query = query.offset((page - 1) * per_page)
            query = query.limit(per_page)

        listing_person_cols = self.db.execute(query).all()

        return listing_person_cols, total
