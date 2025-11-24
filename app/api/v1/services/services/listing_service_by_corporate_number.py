from sqlalchemy.sql import text
from sqlmodel import Session, select

from app.api.v1.schemas.users import UserBase
from app.models import TeamCompany
from app.models.team import PlanCode


def listing_service_by_corporate_number(
    corporate_number: str,
    db: Session,
    per_page: int,
    page: int,
    current_user: UserBase,
    listing_plan_code: PlanCode,
):
    company_downloaded = None
    if listing_plan_code != PlanCode.UNLIMITED:
        company_downloaded = db.exec(
            select(TeamCompany).where(
                TeamCompany.corporate_number == corporate_number,
                TeamCompany.team_id == current_user.team_id,
            )
        ).first()

    if company_downloaded is None:
        per_page = 5
        page = 1

    query = """SELECT *
        FROM company_services
        WHERE :corporate_number = ANY(corporate_number)
        AND (
        COALESCE(NULLIF(TRIM(name), ''), '') <> '' OR
        COALESCE(NULLIF(TRIM(description), ''), '') <> '' OR
        COALESCE(NULLIF(TRIM(title), ''), '') <> '' OR
        (name_tags IS NOT NULL AND CARDINALITY(name_tags) > 0)
      )
        ORDER BY updated_at DESC NULLS LAST, id DESC
        LIMIT :limit OFFSET :offset
    """
    services = db.execute(
        text(query),
        {
            "corporate_number": corporate_number,
            "limit": per_page,
            "offset": (page - 1) * per_page,
        },
    ).all()

    results = []

    for row in services:
        data = dict(row)

        if not data["name"] or not str(data["name"]).strip():
            data["name"] = None

        if data["title"] and data["title"].strip():
            data["name"] = data["title"]

        results.append(data)

    count_query = """SELECT COUNT(*) as total
        FROM company_services
        WHERE :corporate_number = ANY(corporate_number)
        AND (
        COALESCE(NULLIF(TRIM(name), ''), '') <> '' OR
        COALESCE(NULLIF(TRIM(description), ''), '') <> '' OR
        COALESCE(NULLIF(TRIM(title), ''), '') <> '' OR
        (name_tags IS NOT NULL AND CARDINALITY(name_tags) > 0)
      )
    """
    total = db.execute(
        text(count_query), {"corporate_number": corporate_number}
    ).scalar()

    unlimited_total = total

    return results, total, unlimited_total
