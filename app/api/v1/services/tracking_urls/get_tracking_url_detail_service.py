from sqlalchemy.sql import text
from sqlmodel import Session

from app.api.base.exceptions import ForbiddenException, NotFoundException
from app.api.v1.schemas.users import UserBase


def get_tracking_url_detail(
    db: Session,
    current_user: UserBase,
    tracking_url_id: int,
):
    query = """SELECT tu.* FROM tracking_urls tu
                    WHERE tu.id = :tracking_url_id"""

    tracking_url = db.execute(
        text(query),
        {
            "tracking_url_id": tracking_url_id,
        },
    ).one()

    if not tracking_url:
        raise NotFoundException(detail="common.notFound")

    if not tracking_url.team_id == current_user.team_id:
        raise ForbiddenException(detail="auth.permissionDenied")

    return tracking_url


def get_clickable_tracking_url_count(db: Session, tracking_url_id: int):
    count_query = """SELECT COUNT(*) FROM url_click_histories ch
                LEFT JOIN tracking_urls tu ON ch.tracking_url_id = tu.id
                WHERE ch.tracking_url_id = :tracking_url_id
                """
    count = (
        db.execute(
            text(count_query),
            {
                "tracking_url_id": tracking_url_id,
            },
        ).scalar()
        or 0
    )
    return count
