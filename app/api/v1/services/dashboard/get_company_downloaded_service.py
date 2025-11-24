from sqlalchemy.sql import text
from sqlmodel import Session

from app.api.v1.schemas.users import UserBase


def count_this_month_downloaded_companies(db: Session, current_user: UserBase):
    query = """ SELECT COUNT(*)
                AS count_downloaded_month
                FROM team_companies tc
                WHERE
                TO_CHAR(tc.created_at, 'YYYY-MM') = TO_CHAR(now(), 'YYYY-MM')
                AND tc.team_id = :team_id
                GROUP BY TO_CHAR(tc.created_at, 'YYYY-MM')"""
    count = db.execute(text(query), {"team_id": current_user.team_id}).scalar()
    if count is None:
        count = 0
    return count


def count_total_downloaded_companies(db: Session, current_user: UserBase):
    query = """ SELECT COUNT(*)
                FROM team_companies tc
                WHERE team_id = :team_id"""
    count = db.execute(text(query), {"team_id": current_user.team_id}).scalar_one()
    return count
