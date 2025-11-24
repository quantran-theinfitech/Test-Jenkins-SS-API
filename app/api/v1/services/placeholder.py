from datetime import datetime
from typing import Optional

from sqlalchemy.sql import text
from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.placeholders import Placeholder, UpsertPlaceholderRequest
from app.api.v1.schemas.users import UserBase
from app.models.placeholder import PlaceHolder
from app.models.placeholder_item import PlaceHolderItem


class PlaceholderService:
    def __init__(self, db: Session):
        self.db = db

    def listing_placeholders(
        self,
        current_user: UserBase,
        page: Optional[int],
        per_page: Optional[int],
        keyword: Optional[str],
    ):

        query_keyword = ""
        if keyword:
            query_keyword = """ AND p.name ILIKE :keyword"""
        query_pagination = ""
        if page and per_page:
            query_pagination = """ LIMIT :limit OFFSET :offset"""
        query = f""" SELECT p.id, max(p.team_id) as team_id, max(p.name) as name,
                    max(p.created_at) as created_at, MAX(u.name) AS created_by,
                    COUNT(fj.id) AS usage_count
                    FROM placeholders p
                    LEFT JOIN users u
                    ON u.id = p.created_by
                    LEFT JOIN form_jobs fj
                    ON fj.placeholder_id = p.id
                    AND fj.team_id = :team_id
                    WHERE p.team_id = :team_id
                    {query_keyword}
                    GROUP BY p.id
                    ORDER BY p.created_at DESC
                    {query_pagination}
                    """
        placeholders = self.db.execute(
            text(query),
            {
                "team_id": current_user.team_id,
                "limit": per_page,
                "offset": (page - 1) * per_page if per_page and page else "",
                "keyword": f"%{keyword}%",
            },
        ).all()
        return placeholders

    def listing_placeholders_count(
        self, current_user: UserBase, keyword: Optional[str]
    ):
        query_keyword = ""
        if keyword:
            query_keyword = """ AND p.name ILIKE :keyword """
        query = f""" SELECT count(*) FROM placeholders p
                    WHERE p.team_id = :team_id
                    {query_keyword}
        """
        total = (
            self.db.execute(
                text(query),
                {
                    "team_id": current_user.team_id,
                    "keyword": f"%{keyword}%",
                },
            ).scalar()
            or 0
        )
        return total

    def get_placeholder_detail(self, placeholder_id: int, current_user: UserBase):

        placeholder_name = self.db.exec(
            select(PlaceHolder.name)
            .where(PlaceHolder.id == placeholder_id)
            .where(PlaceHolder.team_id == current_user.team_id)
        ).one()

        placeholder_items = self.db.exec(
            select(PlaceHolderItem.attr_name, PlaceHolderItem.attr_value)
            .join(PlaceHolder, PlaceHolder.id == PlaceHolderItem.placeholder_id)
            .where(PlaceHolder.team_id == current_user.team_id)
            .where(PlaceHolderItem.placeholder_id == placeholder_id)
        ).all()

        if not placeholder_items:
            raise NotFoundException(detail="common.notFound")
        name = placeholder_name
        placeholder_item = {
            item["attr_name"]: item["attr_value"] for item in placeholder_items
        }
        placeholder = Placeholder(**placeholder_item)
        return name, placeholder

    def create_placeholder(
        self, placeholder_request: UpsertPlaceholderRequest, current_user: UserBase
    ):
        try:
            placeholder = PlaceHolder(
                name=placeholder_request.name,
                team_id=current_user.team_id,
                created_by=current_user.id,
            )
            self.db.add(placeholder)
            self.db.flush()
            self.db.refresh(placeholder)

            placeholder_items = [
                PlaceHolderItem(
                    placeholder_id=placeholder.id,
                    attr_name=name,
                    attr_value=value,
                    created_by=current_user.id,
                )
                for name, value in vars(placeholder_request.placeholder).items()
            ]
            self.db.bulk_save_objects(placeholder_items)
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            raise e

        return placeholder.id

    def update_placeholder(
        self,
        placeholder_id: int,
        placeholder_request: UpsertPlaceholderRequest,
        current_user: UserBase,
    ):
        try:
            now = datetime.now()
            placeholder = self.db.exec(
                select(PlaceHolder)
                .where(PlaceHolder.team_id == current_user.team_id)
                .where(PlaceHolder.id == placeholder_id)
            ).one()

            placeholder.name = placeholder_request.name
            placeholder.updated_by = current_user.id
            placeholder.updated_at = now

            self.db.flush()

            placeholder_items = self.db.exec(
                select(PlaceHolderItem)
                .join(PlaceHolder, PlaceHolder.id == PlaceHolderItem.placeholder_id)
                .where(PlaceHolder.team_id == current_user.team_id)
                .where(PlaceHolderItem.placeholder_id == placeholder_id)
                .where(
                    PlaceHolderItem.attr_name.in_(
                        vars(placeholder_request.placeholder).keys()
                    )
                )
            ).all()

            for item in placeholder_items:
                item.attr_value = vars(placeholder_request.placeholder)[item.attr_name]
                item.updated_by = current_user.id
                item.updated_at = now

            self.db.commit()
            self.db.expire_all()

        except Exception as e:
            self.db.rollback()
            raise e

        result = {item.attr_name: item.attr_value for item in placeholder_items}

        return result
