from datetime import datetime

import pytz
from sqlmodel import Session, and_, or_, select

from app.api.v1.schemas.plans import PlanDetailResponse
from app.models.plan import Plan, PlanServiceCode
from app.models.subcription import Subcription
from app.models.team import PlanCode


def get_plan_detail(db: Session, team_id: int) -> PlanDetailResponse:
    data = db.exec(
        select(Plan, Subcription)
        .join(
            Subcription,
            and_(
                Subcription.plan_code == Plan.name_code,
                Subcription.team_id == team_id,
            ),
        )
        .where(Subcription.is_active)
        .where(
            or_(
                Subcription.expire_at > datetime.now(),
                Subcription.plan_code == PlanCode.FRE,
            )
        )
        .where(Plan.service_code == PlanServiceCode.LISTING)
    ).first()
    plan, subcription = data
    now = datetime.now(pytz.timezone("Asia/Tokyo"))
    current_month = now.month
    if subcription.expire_at and subcription.expire_at.timestamp() > now.timestamp():
        if (
            subcription.start_at.replace(month=current_month).timestamp()
            > now.timestamp()
        ):
            start_at = subcription.start_at
        else:
            start_at = subcription.start_at.replace(month=current_month)
        expire_at = subcription.expire_at
    elif (
        not subcription.expire_at
        and subcription.start_at.replace(month=current_month).timestamp()
        > now.timestamp()
    ) or (
        subcription.expire_at and subcription.expire_at.timestamp() < now.timestamp()
    ):
        start_at = subcription.start_at
        expire_at = subcription.start_at.replace(month=current_month)
    else:
        start_at = subcription.start_at.replace(month=current_month)
        expire_at = subcription.start_at.replace(month=current_month + 1)

    return PlanDetailResponse(
        name_code=plan.name_code,
        unlock_cpn_quota=plan.unlock_cpn_quota,
        send_form_quota=plan.send_form_quota,
        max_active_scenarios_number=plan.max_active_scenarios_number,
        unlock_person_quota=plan.unlock_person_quota,
        send_email_quota=plan.send_email_quota,
        download_csv_quota=plan.download_csv_quota,
        telesale_quota=plan.telesale_quota,
        price=plan.price,
        contract_month=plan.contract_month,
        start_at=start_at,
        expire_at=expire_at,
        linkedin_connect_quota=plan.linkedin_connect_quota,
        linkedin_message_quota=plan.linkedin_msg_quota,
    )
