from sqlalchemy import text
from sqlmodel import Session

from app.api.v1.schemas.users import UserBase


def listing_contacts(db: Session, user: UserBase, page: int, per_page: int):
    paginate_query = " LIMIT :per_page OFFSET :offset"
    query = f"""SELECT * FROM contacts c
                WHERE c.team_id = :team_id
                ORDER BY name ASC
                {paginate_query}
                """
    contacts = db.execute(
        text(query),
        {
            "per_page": per_page,
            "offset": (page - 1) * per_page,
            "team_id": user.team_id,
        },
    ).all()

    return contacts


def listing_contacts_count(db: Session, user: UserBase):
    query = f"""SELECT COUNT(*) FROM contacts c
                WHERE c.team_id = {user.team_id}
                """

    count = db.execute(text(query)).scalar() or 0
    return count
