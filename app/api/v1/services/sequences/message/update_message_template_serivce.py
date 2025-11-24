# flake8: noqa: E501
from sqlmodel import Session, delete, exists, select, update

from app.api.base.exceptions import BadRequestException
from app.api.v1.schemas.sequence.message import UpdateMessageTemplateRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.media import media_service
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.content_items import ContentItemsType, SequenceStepContentItem
from app.models.sequence.content_template import SequenceStepContentTemplate
from app.models.sequence.mail_history import MailHistoryStatus, SequenceMailHistory
from app.models.sequence.step import SequenceCampaignStep, StepType
from app.models.team_credit import ServiceCode
from external.s3 import S3Service
from utils.credit_utils import is_enough_credit

# Constants
MAX_TEXT_CHARS = 6000
MAX_TOTAL_SIZE_BYTES = 15 * 1024 * 1024  # 15MB
ALLOWED_FILE_TYPES = {
    # Images
    "image/jpeg",  # .jpeg, .jpg
    "image/png",  # .png
    "image/gif",  # .gif
    "image/webp",  # .webp
    # Documents
    "application/pdf",  # .pdf
    "text/plain",  # .txt
    "application/msword",  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/rtf",  # .rtf
    "application/vnd.oasis.opendocument.text",  # .odt
    # Spreadsheets
    "application/vnd.ms-excel",  # .xls
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "text/csv",  # .csv
    "application/vnd.oasis.opendocument.spreadsheet",  # .ods
    # Presentations
    "application/vnd.ms-powerpoint",  # .ppt
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
    "application/vnd.oasis.opendocument.presentation",  # .odp
    # Archives
    "application/zip",  # .zip
    "application/x-rar-compressed",  # .rar
    "application/x-7z-compressed",  # .7z
    "application/x-tar",  # .tar
    "application/gzip",  # .gz
    # Audio
    "audio/mpeg",  # .mp3
    "audio/wav",  # .wav
    "audio/flac",  # .flac
    "audio/aac",  # .aac
    "audio/ogg",  # .ogg
    # Others
    "application/xml",  # .xml
    "application/json",  # .json
    "application/sql",  # .sql
    "text/x-log",  # .log
    # Videos
    "video/mp4",  # .mp4
}

s3_client = S3Service()


def update_message_template_service(
    db: Session,
    current_user: UserBase,
    message_template_id: int,
    request: UpdateMessageTemplateRequest,
):
    template_exist = db.exec(
        select(SequenceCampaign).where(
            exists(
                select(SequenceCampaignStep).where(
                    SequenceCampaignStep.content_template_id == message_template_id,
                    SequenceCampaignStep.sequence_campaign_id == SequenceCampaign.id,
                    SequenceCampaign.team_id == current_user.team_id,
                    SequenceCampaign.deleted_at.is_(None),
                )
            )
        )
    ).first()

    if not template_exist:
        raise BadRequestException("message.templateNotFound")

    template, step = db.exec(
        select(SequenceStepContentTemplate, SequenceCampaignStep)
        .join(
            SequenceCampaignStep,
            SequenceCampaignStep.content_template_id == SequenceStepContentTemplate.id,
        )
        .where(SequenceStepContentTemplate.id == message_template_id)
    ).first()
    # Update SCHEDULED record's content, title in mail_history TABLE if exist
    mail_histories = db.exec(
        select(SequenceMailHistory).where(
            SequenceMailHistory.sequence_step_id == step.id,
            SequenceMailHistory.status == MailHistoryStatus.SCHEDULED,
        )
    ).all()
    if mail_histories:
        db.execute(
            update(SequenceMailHistory)
            .where(
                SequenceMailHistory.sequence_step_id == step.id,
                SequenceMailHistory.status == MailHistoryStatus.SCHEDULED,
            )
            .values(title=request.title)
        )
    # luu title
    if request.title is not None:
        template.title = request.title
    content_items = []
    previous_content = template.content
    for message_item in request.message_items:
        if message_item.type == ContentItemsType.TEXT:
            db.execute(
                update(SequenceMailHistory)
                .where(
                    SequenceMailHistory.sequence_step_id == step.id,
                    SequenceMailHistory.status == MailHistoryStatus.SCHEDULED,
                )
                .values(content=message_item.content)
            )
            template.content = message_item.content
            if previous_content is None and message_item.content is not None:
                step.is_active = True
            elif not message_item.content:
                step.is_active = False
        else:
            if previous_content is None and (
                message_item.file_path or message_item.file_name
            ):
                step.is_active = True
            elif not previous_content and not (
                message_item.file_path or message_item.file_name
            ):
                step.is_active = False
        if message_item.file_path:
            file_path = media_service.move_file_from_tmp_to_perm(message_item.file_path)
        else:
            file_path = None
        content_items.append(
            SequenceStepContentItem(
                step_content_template_id=message_template_id,
                content=message_item.content,
                type=message_item.type,
                order=message_item.order,
                file_name=message_item.file_name,
                file_path=file_path,
            )
        )
    service_code_pair = {
        StepType.MAIL_AUTO: ServiceCode.EMAIL,
        StepType.MAIL_MANUAL: ServiceCode.EMAIL,
        StepType.LINKEDIN_AUTO_MESSAGE: ServiceCode.LINKEDIN_MSG,
        StepType.LINKEDIN_CONNECTION_REQUEST: ServiceCode.LINKEDIN_MSG,
        StepType.LINKEDIN_VIEW_PROFILE: ServiceCode.LINKEDIN_MSG,
    }
    if not is_enough_credit(
        db, current_user.team_id, 1, service_code_pair[step.step_type]
    ):
        step.is_active = False
    db.add(template)
    db.add(step)
    # Delete existing content items
    db.execute(
        delete(SequenceStepContentItem).where(
            SequenceStepContentItem.step_content_template_id == message_template_id,
            SequenceStepContentItem.deleted_at.is_(None),
        )
    )
    if content_items:
        db.add_all(content_items)
    db.commit()

    return True
