from sqlmodel import Session
from fastapi import APIRouter, Depends

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies.authentication import get_current_user
from app.api.v1.schemas.sequence.mail_templates import (
    DetailMailTemplateResponse,
    UpdateMailTemplateRequest,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.mail_templates import (
    update_mail_template_service,
)
from app.api.v1.services.sequences.mail_templates.get_mail_template_service import (
    detail_mail_template_service,
)

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/{sequence_id}/mail_templates")
def get_sequence_mail_templates(
    sequence_id: int,
):
    return 1


@router.post("/{sequence_id}/mail_templates")
def create_sequence_mail_templates(
    sequence_id: int,
):
    return 1


@router.get(
    "/mail_templates/{mail_template_id}", response_model=DetailMailTemplateResponse
)
def get_mail_templates_details(
    mail_template_id: int,
    db: Session = Depends(get_session),
):
    return detail_mail_template_service(db, mail_template_id)


@router.put("/mail_templates/{mail_template_id}")
def update_mail_templates(
    mail_template_id: int,
    request: UpdateMailTemplateRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return update_mail_template_service(db, current_user, mail_template_id, request)
