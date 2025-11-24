from sqlmodel import Session, and_, exists, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.users import UserBase
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.content_template import SequenceStepContentTemplate
from app.models.sequence.step import SequenceCampaignStep


def get_note_template_service(
    db: Session, current_user: UserBase, note_template_id: int
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
    return note_template
