from sqlmodel import Session, exists, select

from app.api.base.exceptions import BadRequestException
from app.api.v1.schemas.sequence.message import (
    GetMessageItemDetailBase,
    GetMessageTemplateDetailResponse,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.media import media_service
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.content_items import SequenceStepContentItem
from app.models.sequence.content_template import SequenceStepContentTemplate
from app.models.sequence.step import SequenceCampaignStep
from external.s3 import S3Service

s3_client = S3Service()


def get_message_template_detail_service(
    db: Session,
    user: UserBase,
    message_template_id: int,
):
    campaign = db.exec(
        select(SequenceCampaign).where(
            exists(
                select(SequenceCampaignStep).where(
                    SequenceCampaignStep.content_template_id == message_template_id,
                    SequenceCampaignStep.sequence_campaign_id == SequenceCampaign.id,
                    SequenceCampaign.team_id == user.team_id,
                    SequenceCampaign.deleted_at.is_(None),
                )
            )
        )
    ).first()
    if not campaign:
        raise BadRequestException("message.templateNotFound")

    template = db.get(SequenceStepContentTemplate, message_template_id)
    content_items = db.exec(
        select(SequenceStepContentItem).where(
            SequenceStepContentItem.step_content_template_id == message_template_id,
            SequenceStepContentItem.deleted_at.is_(None),
        )
    ).all()
    message_items = []
    for content_item in content_items:
        if content_item.file_path:
            metadata = s3_client.get_object_metadata(content_item.file_path)
            content_size = metadata["ContentLength"] if metadata else None
            mime_type = metadata["ContentType"] if metadata else None
        else:
            content_size = None
            mime_type = None
        message_items.append(
            GetMessageItemDetailBase(
                id=content_item.id,
                type=content_item.type,
                content=content_item.content,
                order=content_item.order,
                file_name=content_item.file_name,
                file_path=media_service.get_presigned_url(content_item.file_path),
                content_size=content_size,
                mime_type=mime_type,
            )
        )

    return GetMessageTemplateDetailResponse(
        id=template.id, title=template.title, message_items=message_items
    )
