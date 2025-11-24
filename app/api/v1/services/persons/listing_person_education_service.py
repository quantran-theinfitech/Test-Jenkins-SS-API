from typing import Optional

from sqlalchemy.sql import text
from sqlmodel import Session

from app.api.v1.schemas.users import UserBase
from app.models.team import PlanCode

from .get_person_by_uuid import get_person_by_uuid


def listing_person_educations(
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
        keyword_query = """AND (pe.school_name ILIKE :keyword)"""

    team_query = ""
    if listing_plan_code is not PlanCode.UNLIMITED:
        team_query = """tp.team_id = :team_id AND """

    query = f"""SELECT pe.*
            FROM person_educations pe
            LEFT JOIN team_persons tp
            ON tp.person_uuid = pe.person_uuid
            WHERE {team_query}
            pe.person_uuid = :person_uuid
            {keyword_query}
            AND (
                CASE
                WHEN EXISTS (
                    SELECT pe2.id
                    FROM person_educations pe2
                    LEFT JOIN team_persons tp ON tp.person_uuid = pe2.person_uuid
                    WHERE {team_query}
                    pe2.person_uuid = :person_uuid
                    AND pe2.media_code = 'LINKEDIN'
                    {keyword_query}
                ) THEN pe.media_code = 'LINKEDIN'
                ELSE pe.media_code = 'WANTEDLY'
                END
            )
            ORDER BY pe.created_at DESC
            """
    if page is not None and per_page is not None:
        query += " LIMIT :per_page OFFSET :offset"
        query_params["per_page"] = per_page
        query_params["offset"] = (page - 1) * per_page
    educations = db.execute(text(query), query_params).all()
    return educations


def count_person_educations(
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
        keyword_query = """AND (pe.school_name ILIKE :keyword)"""

    team_query = ""
    if listing_plan_code is not PlanCode.UNLIMITED:
        team_query = """tp.team_id = :team_id AND """

    count_query = f"""SELECT COUNT(pe.*)
            FROM person_educations pe
            LEFT JOIN team_persons tp
            ON tp.person_uuid = pe.person_uuid
            WHERE {team_query}
            pe.person_uuid = :person_uuid
            {keyword_query}
            AND (
                CASE
                WHEN EXISTS (
                    SELECT pe2.id
                    FROM person_educations pe2
                    LEFT JOIN team_persons tp ON tp.person_uuid = pe2.person_uuid
                    WHERE {team_query}
                    pe2.person_uuid = :person_uuid
                    AND pe2.media_code = 'LINKEDIN'
                    {keyword_query}
                ) THEN pe.media_code = 'LINKEDIN'
                ELSE pe.media_code = 'WANTEDLY'
                END
            )
            """
    educations = db.execute(text(count_query), query_params).scalar() or 0
    return educations
