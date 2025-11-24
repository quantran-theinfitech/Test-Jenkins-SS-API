from sqlalchemy.sql import text
from sqlmodel import Session

from app.models.team import PlanCode
from app.models.team_credit import ServiceCode


def remaining_credit(
    db: Session,
    team_id: int,
    service_code: ServiceCode = ServiceCode.CPN,
) -> float:
    amount_query = """
            SELECT SUM(amount) as amount,
                   SUM(used_amount) as used_amount
            FROM team_credits
            WHERE service_code= :service_code_name
                AND team_id=:team_id
                AND start_at <= now()
                AND end_at >= now()
                AND is_active = true
            GROUP BY team_id
        """
    result = db.execute(
        text(amount_query), {"service_code_name": service_code.name, "team_id": team_id}
    ).first()

    amount, used_amount = result if result else (0, 0)

    return amount - used_amount


def is_company_downloaded(
    db: Session, listing_plan_code: PlanCode, team_id: int, corporate_number: str
):
    if listing_plan_code == PlanCode.UNLIMITED:
        return True
    query_team_company = """SELECT tc.id FROM team_companies tc
                            WHERE tc.corporate_number = :corporate_number
                            AND tc.team_id = :team_id"""
    downloaded_company = db.execute(
        text(query_team_company),
        {
            "team_id": team_id,
            "corporate_number": corporate_number,
        },
    ).first()
    if downloaded_company:
        return True
    else:
        return False


def remaining_active_scenario(db: Session, team_id: int):
    created_active_scenario_count_query = """
        SELECT COUNT(*) FROM scenarios
        WHERE team_id = :team_id
            AND (email_notification_flag = TRUE
            OR slack_notification_flag = TRUE)
    """
    created_active_scenario_count = (
        db.execute(
            text(created_active_scenario_count_query), {"team_id": team_id}
        ).scalar()
        or 0
    )

    max_active_scenarios_query = """
    SELECT sum(tb.amount) FROM (
        SELECT DISTINCT tc.id, tc.amount
        FROM team_credits tc
        JOIN  subcriptions s
        ON s.team_id = :team_id
        AND tc.service_code = 'SCENARIO'
        WHERE s.service_code = 'LISTING'
        AND s.plan_code = 'PRE'
        AND s.expire_at > now()
        ) as tb
    """

    max_active_scenarios_number = (
        db.execute(text(max_active_scenarios_query), {"team_id": team_id}).scalar() or 0
    )

    return max_active_scenarios_number - created_active_scenario_count
