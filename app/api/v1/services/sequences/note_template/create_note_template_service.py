from sqlmodel import Session, and_, exists, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.sequence.note import CreateNoteRequest
from app.api.v1.schemas.users import UserBase
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.content_template import (
    ContentType,
    SequenceStepContentTemplate,
)
from app.models.sequence.step import SequenceCampaignStep


def create_note_template_service(
    db: Session, current_user: UserBase, request: CreateNoteRequest
):
    try:
        campaign = db.exec(
            select(SequenceCampaign).where(
                exists().where(
                    and_(
                        SequenceCampaignStep.sequence_campaign_id
                        == SequenceCampaign.id,
                        SequenceCampaignStep.id == request.step_id,
                    )
                )
            )
        ).first()
        if not campaign:
            raise NotFoundException("Campaign not found")
        if campaign.team_id != current_user.team_id:
            raise NotFoundException("Campaign not found")
        step = db.get(SequenceCampaignStep, request.step_id)
        if not step:
            raise NotFoundException("Step not found")
        note_template = SequenceStepContentTemplate(
            content_type=ContentType.NOTE, content=request.content
        )

        db.add(note_template)
        db.flush()
        step.content_template_id = note_template.id
        db.add(step)

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
