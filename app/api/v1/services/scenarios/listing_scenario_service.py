from typing import Optional

from sqlalchemy.sql import text
from sqlmodel import Session

from app.api.v1.schemas.users import UserBase
from app.models.scenario import TypeCode


def listing_scenarios(
    db: Session,
    current_user: UserBase,
    keyword: Optional[str] = None,
    typeCode: Optional[TypeCode] = None,
):

    keyword_query = ""
    if keyword:
        keyword_query = """AND s.name ILIKE :name"""

    # Filter scenario by tab | typeCode (recruit| news | technology)
    if typeCode:
        keyword_query = f"""{keyword_query} AND s.type_code = '{typeCode}'"""

    query = (
        f"""SELECT s.* FROM scenarios s WHERE s.team_id = :team_id {keyword_query} """
    )

    listing_scenarios = db.execute(
        text(query), {"name": f"%{keyword}%", "team_id": current_user.team_id}
    ).all()
    return listing_scenarios
