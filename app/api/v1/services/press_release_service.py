from sqlalchemy.sql import text
from sqlmodel import Session

from app.models.press_release import PressRelease
from app.models.team import PlanCode
from utils.extract_domain import extract_domain


class PressReleaseService:
    def __init__(self, db: Session):
        self.db = db

    def listing_press_releases(self, corporate_number: str, per_page: int, page: int):
        press_releases = (
            self.db.query(PressRelease)
            .filter(PressRelease.corporate_number == corporate_number)
            .order_by(PressRelease.posted_at.desc().nulls_last())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return press_releases

    def get_press_releases_count(self, corporate_number: str):
        count_query = """SELECT COUNT(pr.corporate_number) FROM press_releases pr
                    WHERE pr.corporate_number = :corporate_number
                    AND pr.title != :title
                    """
        total = (
            self.db.execute(
                text(count_query),
                {
                    "corporate_number": corporate_number,
                    "title": "メディアユーザー限定の記事となります。",
                },
            ).scalar()
            or 0
        )
        return total

    def listing_press_releases_by_domain(self, url: str, listing_plan_code):
        domain = extract_domain(url)
        if listing_plan_code == PlanCode.UNLIMITED:
            query = """ SELECT pr.*
                        FROM press_releases pr
                        LEFT JOIN companies c
                        ON c.corporate_number = pr.corporate_number
                        WHERE c."domain" = :domain
                        ORDER BY pr.posted_at DESC
                        LIMIT 10"""
        else:
            query = """ SELECT pr.*
                        FROM team_companies tc
                        LEFT JOIN companies c
                        ON c.corporate_number = tc.corporate_number
                        LEFT JOIN press_releases pr
                        ON tc.corporate_number = pr.corporate_number
                        WHERE c."domain" = :domain
                        ORDER BY pr.posted_at DESC
                        LIMIT 10"""
        data = self.db.execute(text(query), {"domain": domain}).all()

        return data
