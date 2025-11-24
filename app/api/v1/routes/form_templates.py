from typing import Optional

from fastapi import APIRouter, Depends

from app.api.base.deps import custom_generate_unique_id
from app.api.v1.dependencies import get_current_user, get_form_template_service
from app.api.v1.schemas.form_templates import (
    FormTemplateBase,
    FormTemplateRequest,
    ListingTemplateResponse,
)
from app.api.v1.services.form_template_service import FormTemplateService
from app.models.user import User

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("", response_model=ListingTemplateResponse)
def listing_form_tempalates(
    form_template_service: FormTemplateService = Depends(get_form_template_service),
    current_user: User = Depends(get_current_user()),
    page: Optional[int] = None,
    per_page: Optional[int] = None,
    keyword: Optional[str] = None,
):
    data = form_template_service.listing_form_templates(
        current_user, page, per_page, keyword
    )
    total = form_template_service.count_listing_form_templates(current_user, keyword)
    return ListingTemplateResponse(per_page=per_page, page=page, total=total, data=data)


@router.get("/{form_template_id}", response_model=FormTemplateBase)
def get_form_template_detail(
    form_template_id: int,
    form_template_sevice: FormTemplateService = Depends(get_form_template_service),
    current_user: User = Depends(get_current_user()),
):
    return form_template_sevice.get_form_template_detail(form_template_id, current_user)


@router.post("", response_model=FormTemplateBase)
def create_form_template(
    request: FormTemplateRequest,
    current_user: User = Depends(get_current_user()),
    form_template_sevice: FormTemplateService = Depends(get_form_template_service),
):
    return form_template_sevice.create_form_template(request, current_user)


@router.patch("/{form_template_id}", response_model=FormTemplateBase)
def edit_form_template(
    form_template_id: int,
    request: FormTemplateRequest,
    current_user: User = Depends(get_current_user()),
    form_template_sevice: FormTemplateService = Depends(get_form_template_service),
):
    return form_template_sevice.edit_form_template(
        form_template_id, request, current_user
    )
