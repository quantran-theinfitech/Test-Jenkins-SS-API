from typing import Optional

from sqlalchemy.sql import text
from sqlmodel import Session


def get_scenario_detail(
    db: Session, id: int, team_id: int, notification_id: Optional[int]
):
    query_notification = ""
    select_updated_at = ""

    if notification_id:
        query_notification = (
            "LEFT JOIN scenario_notifications sn ON sn.id = :notification_id "
        )
        select_updated_at = ", sn.updated_at AS notification_updated_at"

    query = f"""
        SELECT s.*{select_updated_at}
        FROM scenarios s
        {query_notification}
        WHERE s.team_id = :team_id AND s.id = :scenario_id
    """
    scenario_detail = db.execute(
        text(query),
        {"scenario_id": id, "team_id": team_id, "notification_id": notification_id},
    ).first()
    return scenario_detail
