from sqlalchemy.sql import text
from sqlmodel import Session

from app.api.v1.schemas.users import UserBase


def count_this_month_sent_forms(db: Session, current_user: UserBase):
    query = """ SELECT COUNT(*)
                FROM form_jobs fj
                WHERE
                TO_CHAR(fj.created_at, 'YYYY-MM') = TO_CHAR(now(), 'YYYY-MM')
                AND fj.team_id = :team_id
                GROUP BY TO_CHAR(fj.created_at, 'YYYY-MM')"""
    count = db.execute(text(query), {"team_id": current_user.team_id}).scalar() or 0
    return count


def count_total_sent_forms(db: Session, current_user: UserBase):
    query = """ SELECT COUNT(*)
                FROM form_jobs fj
                WHERE fj.team_id = :team_id"""
    count = db.execute(text(query), {"team_id": current_user.team_id}).scalar() or 0
    return count
