from datetime import datetime

from sqlmodel import Session, select, update

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.sequence.mail_templates import UpdateMailTemplateRequest
from app.api.v1.schemas.users import UserBase
from app.models.sequence.content_template import (
    ContentType,
    SequenceStepContentTemplate,
)
from app.models.sequence.mail_history import MailHistoryStatus, SequenceMailHistory
from app.models.sequence.step import SequenceCampaignStep


def update_mail_template_service(
    db: Session,
    current_user: UserBase,
    mail_template_id: int,
    request: UpdateMailTemplateRequest,
):
    template, current_step = db.exec(
        select(SequenceStepContentTemplate, SequenceCampaignStep)
        .join(
            SequenceCampaignStep,
            SequenceStepContentTemplate.id == SequenceCampaignStep.content_template_id
            )
        .where(
            SequenceStepContentTemplate.id == mail_template_id,
            SequenceStepContentTemplate.deleted_at.is_(None),
            SequenceStepContentTemplate.content_type == ContentType.MAIL,
        )
    ).first()
    if not template:
        raise NotFoundException("mail template not found")

    for attr, value in request.dict(exclude_unset=True).items():
        setattr(template, attr, value)
    template.updated_by = current_user.id
    template.updated_at = datetime.now()
    #update scheduled task title, content
    db.exec(
        update(SequenceMailHistory)
        .where(
            SequenceMailHistory.sequence_step_id == current_step.id,
            SequenceMailHistory.status == MailHistoryStatus.SCHEDULED
        ).values(
            content=template.content,
            title=template.title
        )
    )
    if template.is_reply_to_previous_thread:
        step = db.exec(
            select(SequenceCampaignStep).where(
                SequenceCampaignStep.content_template_id == mail_template_id
            )
        ).first()
        prev_step_mail_template = db.exec(
            select(SequenceStepContentTemplate)
            .join(
                SequenceCampaignStep,
                SequenceStepContentTemplate.id
                == SequenceCampaignStep.content_template_id,
            )
            .where(
                SequenceCampaignStep.sequence_campaign_id == step.sequence_campaign_id,
                SequenceCampaignStep.order == step.order - 1,
                SequenceCampaignStep.deleted_at.is_(None),
            )
        ).first()
        if prev_step_mail_template and prev_step_mail_template.title:
            template.title = prev_step_mail_template.title
    db.add(template)
    db.flush()
    db.refresh(template)
    if not template.title:
        step = db.exec(
            select(SequenceCampaignStep).where(
                SequenceCampaignStep.content_template_id == mail_template_id
            )
        ).first()

        if step:
            step.is_active = False
            db.add(step)
            db.flush()
            db.refresh(step)

    db.commit()
    return template.id
