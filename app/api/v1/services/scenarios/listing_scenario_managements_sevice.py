from sqlalchemy.sql import text
from sqlmodel import Session


def listing_scenario_managements(db: Session, per_page: int, page: int, team_id: int):
    query = """SELECT s.id, s.name, s.type_code, s.description,
        s.target_email, s.target_slack_connection_id,
        s.email_notification_flag, s.slack_notification_flag,
        max(u.name) as created_by,
        max(sc.channel_name) as channel_name,
        COUNT(CASE WHEN sni.created_at
        BETWEEN date_trunc('day', current_date)
        AND now() THEN sni.id END) AS today_count,
        COUNT(CASE WHEN sni.created_at
        BETWEEN date_trunc('day', current_date - interval '1 day')
        AND date_trunc('day', current_date) THEN sni.id END)
        AS yesterday_count,
        COUNT(CASE WHEN sni.created_at
        BETWEEN date_trunc('day', current_date - interval '7 day')
        AND now() THEN sni.id END)
        AS last_7_days_count
        FROM scenarios s
        LEFT JOIN scenario_notifications sn ON sn.scenario_id =s.id
        LEFT JOIN scenario_notification_items sni
        ON sni.scenario_notification_id = sn.id
        LEFT JOIN slack_connections sc
        ON sc.id = s.target_slack_connection_id
        LEFT JOIN users u on u.id = s.created_by
        WHERE s.team_id = :team_id
        GROUP BY s.id
        ORDER BY s.created_at DESC
        LIMIT :limit OFFSET :offset
                """
    scenario = db.execute(
        text(query),
        {
            "team_id": team_id,
            "limit": per_page,
            "offset": (page - 1) * per_page,
        },
    ).all()
    return scenario


def listing_scenario_managements_count(db: Session, team_id: int):
    query = """SELECT COUNT(s.*) FROM scenarios s
                WHERE s.team_id = :team_id
                """
    total = db.execute(text(query), {"team_id": team_id}).scalar() or 0
    return total
