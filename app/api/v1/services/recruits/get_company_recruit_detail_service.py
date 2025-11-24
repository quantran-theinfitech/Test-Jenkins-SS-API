from sqlalchemy.sql import text
from sqlmodel import Session

from app.api.base.exceptions import ForbiddenException
from app.api.v1.services.base_service import is_company_downloaded
from app.models.team import PlanCode
from app.models.user import User


def get_company_recruit_detail(
    db: Session,
    current_user: User,
    listing_plan_code: PlanCode,
    recruit_id: int,
):
    query = """SELECT r.*, c.postal_code
            FROM recruits r
            JOIN companies c ON r.corporate_number = c.corporate_number
            WHERE r.id = :recruit_id"""
    recruit = db.execute(
        text(query),
        {
            "recruit_id": recruit_id,
        },
    ).one()
    if not is_company_downloaded(
        db, listing_plan_code, current_user.team_id, recruit.corporate_number
    ):
        raise ForbiddenException(detail="auth.permissionDenied")
    else:

        return recruit
