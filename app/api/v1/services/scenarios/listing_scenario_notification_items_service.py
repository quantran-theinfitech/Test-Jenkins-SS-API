from sqlalchemy.sql import text
from sqlmodel import Session

from app.api.base.exceptions import NotFoundException


def listing_scenario_notification_items(
    db: Session, id: int, per_page: int, page: int, team_id: int
):
    query_scenario = """SELECT s.id FROM scenario_notifications sn
                        LEFT JOIN scenarios s ON s.id = sn.scenario_id
                        WHERE sn.id = :notification_id AND s.team_id = :team_id"""
    query_scenario_id = db.execute(
        text(query_scenario),
        {
            "team_id": team_id,
            "notification_id": id,
        },
    ).scalar()
    if query_scenario_id is None:
        raise NotFoundException(detail="common.notFound")
    else:
        query = """SELECT sni.id, sni.created_at, r.title ,
            r.media_code , c."name", r.small_category, c.corporate_number,
            r.large_category, r.medium_category, r.recruit_tels,
            r.recruit_mails, c.phone as company_tel,r.source_recruit_url,
            c.contact_email, c.hp_url, c.contact_form_url,
            c.president_name, c.industry_code as large_industry
            FROM scenario_notification_items sni
            LEFT JOIN recruits r ON r.media_code = sni.media_code
                AND r.media_internal_id = sni.media_internal_id
            LEFT JOIN companies c ON c.corporate_number = r.corporate_number
            WHERE sni.scenario_notification_id = :notification_id
            ORDER BY r.created_at DESC
            LIMIT :limit OFFSET :offset;
            """
        scenario_notification_items = db.execute(
            text(query),
            {
                "notification_id": id,
                "limit": per_page,
                "offset": (page - 1) * per_page,
            },
        ).all()
        return scenario_notification_items


def listing_scenario_notification_items_count(db: Session, id: int):
    query = """SELECT count(sni.*) FROM scenario_notification_items sni
                WHERE sni.scenario_notification_id = :notification_id
                """
    total = (
        db.execute(
            text(query),
            {
                "notification_id": id,
            },
        ).scalar()
        or 0
    )
    return total
