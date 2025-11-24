from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.v1.schemas.sequence.mail_templates import DetailMailTemplateResponse
from app.models.sequence.content_template import (
    ContentType,
    SequenceStepContentTemplate,
)
from app.models.sequence.step import SequenceCampaignStep


def detail_mail_template_service(
    db: Session,
    mail_template_id: int,
):
    result = db.exec(
        select(SequenceStepContentTemplate, SequenceCampaignStep)
        .select_from(SequenceStepContentTemplate)
        .join(
            SequenceCampaignStep,
            SequenceCampaignStep.content_template_id == mail_template_id,
            SequenceStepContentTemplate.content_type == ContentType.MAIL,
        )
        .where(
            SequenceStepContentTemplate.id == mail_template_id,
            SequenceStepContentTemplate.deleted_at.is_(None),
            SequenceCampaignStep.deleted_at.is_(None),
        )
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="sequence.stepNotFound")
    template, step_on_template = result
    return DetailMailTemplateResponse(
        **template.dict(), total_days_on_step=step_on_template.total_days
    )
