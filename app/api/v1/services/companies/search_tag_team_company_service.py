from sqlalchemy import text
from sqlmodel import Session

from app.api.v1.schemas.users import UserBase


def search_tag_team_company(
    tag: str,
    db: Session,
    current_user: UserBase,
):
    tagCondition = ""
    if tag is not None:
        tagCondition = "WHERE t.tag ILIKE :tag"
    else:
        tagCondition = "ORDER BY t.created_at DESC LIMIT 5"
    query = f"""
        WITH tags as (
            SELECT DISTINCT tag
            FROM team_companies tc
            CROSS JOIN unnest(tags) AS tag
            WHERE tc.team_id = :team_id
        )
        SELECT t.tag
        FROM tags t
        {tagCondition}
        """
    tags = db.execute(
        text(query),
        {
            "team_id": current_user.team_id,
            "tag": f"%{tag}%",
        },
    ).all()
    return ["".join(tag) for tag in tags]
