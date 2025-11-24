from sqlalchemy.sql import text
from sqlmodel import Session


def listing_scenario_notifications(
    db: Session, id: int, per_page: int, page: int, team_id: int
):
    query_scenario_notifications = """SELECT sn.id, max(s.target_email)
        AS target_email, max(sc.channel_name) as channel_name ,
        sn.created_at, sn.email_notify_at, sn.slack_notify_at,
        count(sni.id) as count_item
        FROM scenario_notifications sn
        LEFT JOIN scenarios s ON s.id = :scenario_id
        LEFT JOIN scenario_notification_items sni
        ON sni.scenario_notification_id = sn.id
        left join slack_connections sc on sc.id = s.target_slack_connection_id
        WHERE sn.scenario_id = :scenario_id AND s.team_id = :team_id
        GROUP BY sn.id
        ORDER BY sn.created_at DESC
        LIMIT :limit OFFSET :offset;
        """
    scenario = db.execute(
        text(query_scenario_notifications),
        {
            "scenario_id": id,
            "limit": per_page,
            "offset": (page - 1) * per_page,
            "team_id": team_id,
        },
    ).all()
    return scenario


def listing_scenario_notifications_count(db: Session, id: int, team_id: int):
    query = """SELECT count(sn.*) FROM scenario_notifications sn
                WHERE sn.scenario_id = :scenario_id
                """
    total = (
        db.execute(
            text(query),
            {
                "scenario_id": id,
            },
        ).scalar()
        or 0
    )
    return total
