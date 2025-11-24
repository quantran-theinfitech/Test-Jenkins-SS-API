from sqlalchemy import and_, func
from sqlmodel import Session, select

from app.models.plan import Plan
from app.models.subcription import Subcription


def get_plan_histories(db: Session, team_id: int, page: int = 1, page_size: int = 10):
    plan_histories = db.exec(
        select(
            Subcription.start_at,
            Subcription.expire_at,
            Subcription.is_active,
            Plan.name_code,
            Plan.price,
            Plan.contract_month,
            Plan.unlock_cpn_quota,
            Plan.unlock_person_quota,
            Plan.send_form_quota,
            Plan.send_email_quota,
            Plan.download_csv_quota,
            Plan.telesale_quota,
            Plan.max_active_scenarios_number,
            Plan.service_code,
        )
        .join(
            Plan,
            and_(
                Subcription.plan_code == Plan.name_code,
                Subcription.service_code == Plan.service_code,
            ),
        )
        .where(
            Subcription.team_id == team_id,
        )
        .order_by(Subcription.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return plan_histories


def get_plan_history_count(db: Session, team_id: int):
    total = (
        db.execute(
            select(func.count(Subcription.id))
            .join(
                Plan,
                and_(
                    Subcription.plan_code == Plan.name_code,
                    Subcription.service_code == Plan.service_code,
                ),
            )
            .where(
                Subcription.team_id == team_id,
            )
        ).scalar()
        or 0
    )

    return total
