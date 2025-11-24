from sqlmodel import Session, and_, exists, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.sequence.note import UpdateNoteRequest
from app.api.v1.schemas.users import UserBase
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.content_template import SequenceStepContentTemplate
from app.models.sequence.step import SequenceCampaignStep


def update_note_template_service(
    db: Session,
    current_user: UserBase,
    note_template_id: int,
    request: UpdateNoteRequest,
):
    campaign = db.exec(
        select(SequenceCampaign).where(
            exists().where(
                and_(
                    SequenceCampaignStep.sequence_campaign_id == SequenceCampaign.id,
                    SequenceCampaignStep.content_template_id == note_template_id,
                )
            )
        )
    ).first()
    if not campaign:
        raise NotFoundException("Campaign not found")
    if campaign.team_id != current_user.team_id:
        raise NotFoundException("Campaign not found")
    note_template = db.get(SequenceStepContentTemplate, note_template_id)
    if not note_template:
        raise NotFoundException("note.notFound")
    note_template.content = request.content
    db.add(note_template)
    db.commit()
    return note_template
