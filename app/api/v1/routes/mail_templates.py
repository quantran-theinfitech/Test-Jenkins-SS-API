from typing import Optional

from fastapi import APIRouter, Depends

from app.api.base.deps import custom_generate_unique_id
from app.api.v1.dependencies import get_current_user, get_mail_template_service
from app.api.v1.schemas.mail_templates import (
    ListingTemplateResponse,
    MailTemplateBase,
    MailTemplateRequest,
)
from app.api.v1.services.mail_template_service import MailTemplateService
from app.models.user import User

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("", response_model=ListingTemplateResponse)
def listing_mail_templates(
    mail_template_service: MailTemplateService = Depends(get_mail_template_service),
    current_user: User = Depends(get_current_user()),
    page: Optional[int] = None,
    per_page: Optional[int] = None,
):
    data = mail_template_service.listing_mail_templates(current_user, page, per_page)
    total = mail_template_service.count_listing_mail_templates(current_user)
    return ListingTemplateResponse(
        per_page=per_page, current_page=page, total=total, data=data
    )


@router.get("/{mail_template_id}", response_model=MailTemplateBase)
def get_mail_template_detail(
    mail_template_id: int,
    mail_template_sevice: MailTemplateService = Depends(get_mail_template_service),
    current_user: User = Depends(get_current_user()),
):
    return mail_template_sevice.get_mail_template_detail(mail_template_id, current_user)


@router.post("", response_model=MailTemplateBase)
def create_mail_template(
    request: MailTemplateRequest,
    current_user: User = Depends(get_current_user()),
    mail_template_sevice: MailTemplateService = Depends(get_mail_template_service),
):
    return mail_template_sevice.create_mail_template(request, current_user)


@router.patch("/{mail_template_id}", response_model=MailTemplateBase)
def edit_mail_template(
    mail_template_id: int,
    request: MailTemplateRequest,
    current_user: User = Depends(get_current_user()),
    mail_template_sevice: MailTemplateService = Depends(get_mail_template_service),
):
    return mail_template_sevice.edit_mail_template(
        mail_template_id, request, current_user
    )
