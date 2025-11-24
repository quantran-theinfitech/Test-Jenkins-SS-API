from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies.authentication import get_current_user
from app.api.v1.schemas.sequence.message import (
    GetMessageTemplateDetailResponse,
    UpdateMessageTemplateRequest,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences import message as message_service

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get(
    "/message_templates/{message_template_id}",
    response_model=GetMessageTemplateDetailResponse,
)
def get_message_templates_details(
    message_template_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return message_service.get_message_template_detail_service(
        db, current_user, message_template_id
    )


@router.put("/message_templates/{message_template_id}")
def update_message_templates(
    message_template_id: int,
    request: UpdateMessageTemplateRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return message_service.update_message_template_service(
        db, current_user, message_template_id, request
    )
