from sqlalchemy.sql import text
from sqlmodel import Session


def listing_event_by_corporate_number(
    corporate_number: str, db: Session, per_page: int, page: int
):
    query = """SELECT e.*
        FROM events e
        WHERE e.corporate_number = :corporate_number
        ORDER BY e.start_time DESC NULLS LAST
        LIMIT :limit OFFSET :offset
    """
    events = db.execute(
        text(query),
        {
            "corporate_number": str(corporate_number),
            "limit": per_page,
            "offset": (page - 1) * per_page,
        },
    ).all()

    count_query = """SELECT COUNT(*) as total
        FROM events e
        WHERE e.corporate_number = :corporate_number
    """
    total = db.execute(
        text(count_query), {"corporate_number": str(corporate_number)}
    ).scalar()

    unlimited_total = total

    return events, total, unlimited_total
