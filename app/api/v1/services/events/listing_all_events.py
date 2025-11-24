from sqlalchemy.sql import text
from sqlmodel import Session


def listing_all_events(db: Session, per_page: int, page: int):
    query = """SELECT e.*
                FROM events e
                ORDER BY e.start_time DESC NULLS LAST
                LIMIT :limit OFFSET :offset
                """
    events = db.execute(
        text(query),
        {
            "limit": per_page,
            "offset": (page - 1) * per_page,
        },
    ).all()
    count_query = """SELECT COUNT(*) as total
        FROM events e
    """
    total = db.execute(text(count_query)).scalar()
    unlimited_total = total
    return events, total, unlimited_total
