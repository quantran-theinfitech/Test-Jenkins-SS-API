from sqlalchemy.sql import text
from sqlmodel import Session

from app.models.user import User


def get_collection_detail(
    db: Session,
    collection_id: int,
    current_user: User,
):
    query = text(
        """SELECT *
            FROM person_collections pc
            WHERE pc.id = :collection_id AND pc.team_id = :team_id
        """
    )

    collection = db.execute(
        query, {"collection_id": collection_id, "team_id": current_user.team_id}
    ).one()
    return collection
