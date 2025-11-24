from sqlmodel import Session, func

from app.api.v1.schemas.recruits import RecruitBase
from app.models.company import Company
from app.models.recruit import Recruit


def listing_company_recruits(
    db: Session, corporate_number: str, per_page: int, page: int
):
    res = []
    postal_code = (
        db.query(Company.postal_code)
        .filter(Company.corporate_number == corporate_number)
        .scalar()
    )
    recruits = (
        db.query(Recruit)
        .filter(Recruit.corporate_number == corporate_number)
        .order_by(Recruit.start_at.desc().nulls_last())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    for recruit in recruits:
        recruit = RecruitBase(
            id=recruit.id,
            title=recruit.title,
            content=recruit.content,
            corporate_number=recruit.corporate_number,
            tags=recruit.tags,
            source_recruit_url=recruit.source_recruit_url,
            employment_type_codes=recruit.employment_type_codes,
            sub_title=recruit.sub_title,
            summary=recruit.summary,
            recruit_tels=recruit.recruit_tels,
            recruit_mails=recruit.recruit_mails,
            media_code=recruit.media_code,
            start_at=recruit.start_at,
            end_at=recruit.end_at,
            postal_code=postal_code,
            recruitment_count=recruit.recruitment_count,
            working_location=recruit.working_location,
            other_info=recruit.other_info,
            created_at=recruit.created_at,
            created_by=recruit.created_by,
            updated_at=recruit.updated_at,
        )
        res.append(recruit)
    return res


def listing_company_recruits_count(db: Session, corporate_number: str):
    recruits_count = (
        db.query(func.count(Recruit.corporate_number))
        .filter(Recruit.corporate_number == corporate_number)
        .scalar()
    )
    return recruits_count
