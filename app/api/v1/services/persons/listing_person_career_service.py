# flake8: noqa: E501

from typing import Optional

from sqlalchemy.sql import text
from sqlmodel import Session

from app.api.v1.schemas.users import UserBase
from app.models.team import PlanCode

from .get_person_by_uuid import get_person_by_uuid


def listing_person_careers(
    person_uuid: str,
    db: Session,
    user: UserBase,
    listing_plan_code: PlanCode,
    keyword: Optional[str] = None,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
):
    get_person_by_uuid(db, person_uuid)

    keyword_query = ""
    query_params = {
        "person_uuid": person_uuid,
        "keyword": f"%{keyword}%",
        "team_id": user.team_id,
    }

    if keyword is not None:
        keyword_query = """AND (pc.role_name ILIKE :keyword)"""
    team_query = ""
    if listing_plan_code is not PlanCode.UNLIMITED:
        team_query = """tp.team_id = :team_id AND """
    query = f"""SELECT DISTINCT ON (pc.role_name, pc.company_name, pc.start_at, pc.end_at, pc.description) pc.*, c.hp_url as hp_url
            FROM person_careers pc
            LEFT JOIN team_persons tp ON tp.person_uuid = pc.person_uuid
            LEFT JOIN companies c ON pc.corporate_number = c.corporate_number
            WHERE {team_query}
            pc.person_uuid = :person_uuid
            {keyword_query}
            AND (
                CASE
                WHEN EXISTS (
                    SELECT pc2.id
                    FROM person_careers pc2
                    LEFT JOIN team_persons tp ON tp.person_uuid = pc2.person_uuid
                    WHERE {team_query}
                    pc2.person_uuid = :person_uuid
                    AND pc2.media_code = 'LINKEDIN'
                    {keyword_query}
                ) THEN pc.media_code = 'LINKEDIN'
                ELSE pc.media_code = 'WANTEDLY'
                END
            )
            ORDER BY pc.role_name, pc.company_name, pc.start_at, pc.end_at, pc.description, pc.created_at DESC
            """

    if page is not None and per_page is not None:
        query += "LIMIT :per_page OFFSET :offset"
        query_params["per_page"] = per_page
        query_params["offset"] = (page - 1) * per_page
    careers = db.execute(text(query), query_params).all()
    return careers, len(careers)


def count_person_careers(
    person_uuid: str,
    db: Session,
    user: UserBase,
    listing_plan_code: PlanCode,
    keyword: Optional[str] = None,
):
    keyword_query = ""
    query_params = {
        "keyword": f"%{keyword}%",
        "team_id": user.team_id,
        "person_uuid": person_uuid,
    }

    if keyword is not None:
        keyword_query = """AND (p.name ILIKE :keyword)"""

    team_query = ""
    if listing_plan_code is not PlanCode.UNLIMITED:
        team_query = """tp.team_id = :team_id AND """

    query = f"""SELECT COUNT(pc.*)
            FROM person_careers pc
            LEFT JOIN team_persons tp ON tp.person_uuid = pc.person_uuid
            WHERE {team_query}
            pc.person_uuid = :person_uuid
            {keyword_query}
            AND (
                CASE
                WHEN EXISTS (
                    SELECT pc2.id
                    FROM person_careers pc2
                    LEFT JOIN team_persons tp ON tp.person_uuid = pc2.person_uuid
                    WHERE {team_query}
                    pc2.person_uuid = :person_uuid
                    AND pc2.media_code = 'LINKEDIN'
                    {keyword_query}
                ) THEN pc.media_code = 'LINKEDIN'
                ELSE pc.media_code = 'WANTEDLY'
                END
            )
            """
    count = db.execute(text(query), query_params).scalar() or 0
    return count
