from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies import get_current_user, get_extension_service
from app.api.v1.schemas.companies import CompanyBase
from app.api.v1.schemas.extensions import FillFormRequest, FillFormResponse
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.extensions import ExtensionService

router = APIRouter()


@router.post("/fill-form", response_model=FillFormResponse)
def fill_form(
    request: FillFormRequest,
    current_user: UserBase = Depends(get_current_user()),
    extension_service: ExtensionService = Depends(get_extension_service),
):
    fill_form = extension_service.fill_form(request.html)
    return FillFormResponse(fill_form=fill_form)


@router.get("/search-company", response_model=CompanyBase)
def search_company(
    company_url: str = Query(default=None),
    current_user: UserBase = Depends(get_current_user()),
    extension_service: ExtensionService = Depends(get_extension_service),
):
    return extension_service.search_company(company_url, current_user)
