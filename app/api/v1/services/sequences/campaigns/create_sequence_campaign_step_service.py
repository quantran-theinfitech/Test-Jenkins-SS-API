import uuid
from datetime import datetime

from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.sequence.campaigns import AddStepRequest
from app.api.v1.schemas.users import UserBase
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.content_template import (
    ContentType,
    SequenceStepContentTemplate,
)
from app.models.sequence.step import SequenceCampaignStep, StepType
from app.models.team_credit import ServiceCode
from utils.credit_utils import is_enough_credit

from .get_sequence_campaign_step_service import get_total_days_count


def create_campaign_step_service(
    db: Session, current_user: UserBase, campaign_id: int, request: AddStepRequest
):
    campaign = db.exec(
        select(SequenceCampaign).where(
            SequenceCampaign.id == campaign_id,
            SequenceCampaign.deleted_at.is_(None),
            SequenceCampaign.team_id == current_user.team_id,
        )
    ).first()
    if not campaign:
        raise NotFoundException("Campaign not found")

    prev_steps = db.exec(
        select(SequenceCampaignStep)
        .where(
            SequenceCampaignStep.sequence_campaign_id == campaign_id,
            SequenceCampaignStep.deleted_at.is_(None),
        )
        .order_by(SequenceCampaignStep.order.asc())
    ).all()
    last_step = prev_steps[-1] if prev_steps else None
    try:
        content_template_id = None
        if request.step_type != StepType.LINKEDIN_VIEW_PROFILE:
            if (
                request.step_type == StepType.MAIL_AUTO
                or request.step_type == StepType.MAIL_MANUAL
            ):
                content_type = ContentType.MAIL

            if request.step_type == StepType.LINKEDIN_AUTO_MESSAGE:
                content_type = ContentType.MESSAGE

            if request.step_type == StepType.LINKEDIN_CONNECTION_REQUEST:
                content_type = ContentType.NOTE

            template = SequenceStepContentTemplate(
                title=("テンプレートの件名" if content_type != ContentType.NOTE else None),
                created_by=current_user.id,
                updated_by=current_user.id,
                content_type=content_type,
            )
            db.add(template)
            db.flush()
            db.refresh(template)
            content_template_id = template.id
        service_code_pair = {
            StepType.MAIL_AUTO: ServiceCode.EMAIL,
            StepType.MAIL_MANUAL: ServiceCode.EMAIL,
            StepType.LINKEDIN_AUTO_MESSAGE: ServiceCode.LINKEDIN_MSG,
            StepType.LINKEDIN_CONNECTION_REQUEST: ServiceCode.LINKEDIN_MSG,
            StepType.LINKEDIN_VIEW_PROFILE: ServiceCode.LINKEDIN_MSG,
        }
        is_active = True
        if not is_enough_credit(
            db, current_user.team_id, 1, service_code_pair[request.step_type]
        ):
            is_active = False
        step = SequenceCampaignStep(
            **dict(request),
            uuid=str(uuid.uuid4()),
            content_template_id=content_template_id,
            sequence_campaign_id=campaign.id,
            created_by=current_user.id,
            updated_by=current_user.id,
            order=last_step.order + 1 if last_step else 1,
            is_active=is_active
        )
        prev_steps.append(step)
        step.total_days = get_total_days_count(prev_steps)
        campaign.updated_at = datetime.now()
        db.add(step)
        db.flush()
        db.refresh(step)

        ret = dict(step)
        db.commit()
        return ret
    except Exception as e:
        db.rollback()
        raise e
