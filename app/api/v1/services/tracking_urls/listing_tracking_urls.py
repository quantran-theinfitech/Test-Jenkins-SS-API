from typing import Optional

from sqlalchemy.sql import text
from sqlmodel import Session

from app.api.v1.schemas.users import UserBase


def listing_tracking_urls(
    db: Session,
    current_user: UserBase,
    page: int,
    per_page: int,
    keyword: Optional[str],
):
    query_keyword = """"""
    if keyword:
        query_keyword = """AND tu.name ILIKE :keyword"""
    query = f"""SELECT tu.id, tu."name", tu.original_url, tu.shorten_path,
                tu.tracking_flag, tu.created_at, tu.created_at, tu.team_id,
                u."name" AS created_by
                FROM tracking_urls tu
                LEFT JOIN users u on
                u.id = tu.created_by
                WHERE tu.team_id = :team_id
                {query_keyword}
                ORDER BY tu.created_at DESC
                LIMIT :limit OFFSET :offset """
    tracking_urls = db.execute(
        text(query),
        {
            "team_id": current_user.team_id,
            "limit": per_page,
            "offset": (page - 1) * per_page,
            "keyword": f"%{keyword}%",
        },
    ).all()
    return tracking_urls


def listing_tracking_urls_count(
    db: Session, current_user: UserBase, keyword: Optional[str]
):
    query_keyword = """"""
    if keyword:
        query_keyword = """AND tu.name ILIKE :keyword"""
    query = f"""SELECT COUNT(tu.*)
                FROM tracking_urls tu
                WHERE tu.team_id = :team_id
                {query_keyword}"""
    total = (
        db.execute(
            text(query),
            {
                "team_id": current_user.team_id,
                "keyword": f"%{keyword}%",
            },
        ).scalar()
        or 0
    )
    return total
