from sqlalchemy.sql import text
from sqlmodel import Session

from app.models.team import PlanCode
from utils.extract_domain import extract_domain


def listing_recruit_by_domain(db: Session, url: str, listing_plan_code):
    domain = extract_domain(url)
    if listing_plan_code == PlanCode.UNLIMITED:
        query = """ SELECT r.*
                    FROM recruits r
                    LEFT JOIN companies c
                    ON c.corporate_number = r.corporate_number
                    WHERE c."domain" = :domain
                    ORDER BY r.created_at DESC
                    LIMIT 10
                    """
    else:
        query = """ SELECT r.*
                    FROM team_companies tc
                    LEFT JOIN recruits r
                    ON r.corporate_number = tc.corporate_number
                    LEFT JOIN companies c
                    ON tc.corporate_number = c.corporate_number
                    WHERE c."domain" = :domain
                    ORDER BY r.created_at DESC
                    LIMIT 10
                    """

    data = db.execute(text(query), {"domain": domain}).all()
    return data
