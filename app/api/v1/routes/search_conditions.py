from typing import List

from fastapi import APIRouter, Depends

from app.api.base.deps import custom_generate_unique_id
from app.api.v1.dependencies import get_current_user, get_search_condition_service
from app.api.v1.schemas.companies import SaveSearchConditionRequest
from app.api.v1.schemas.search_conditions import (
    RefineQueryRequest,
    RefineQueryResponse,
    SearchConditionBase,
    UpdateSearchConditionRequest,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.search_condition_service import SearchConditionService
from app.models.search_condition import SearchCondition

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("", response_model=List[SearchConditionBase])
def listing_search_conditions(
    current_user: UserBase = Depends(get_current_user()),
    search_condition_service: SearchConditionService = Depends(
        get_search_condition_service
    ),
):
    return search_condition_service.listing_search_conditions(current_user)


@router.post("/save-search-condition", response_model=SearchCondition)
def save_search_condition(
    condition_request: SaveSearchConditionRequest,
    current_user: UserBase = Depends(get_current_user()),
    search_condition_service: SearchConditionService = Depends(
        get_search_condition_service
    ),
):
    return search_condition_service.save_search_condition(
        condition_request, current_user
    )


@router.get("/condition/{condition_id}", response_model=SearchConditionBase)
def get_search_company_condition_detail(
    condition_id: int,
    current_user: UserBase = Depends(get_current_user()),
    search_condition_service: SearchConditionService = Depends(
        get_search_condition_service
    ),
):
    return search_condition_service.get_search_condition_detail(
        condition_id, current_user
    )


@router.delete("/{search_condition_id}")
def delete_search_condition(
    search_condition_id: int,
    current_user: UserBase = Depends(get_current_user()),
    search_condition_service: SearchConditionService = Depends(
        get_search_condition_service
    ),
):
    return search_condition_service.delete_search_condition(
        search_condition_id, current_user
    )


@router.patch("/{search_condition_id}", response_model=SearchConditionBase)
def update_search_condition(
    search_condition_id: int,
    request: UpdateSearchConditionRequest,
    current_user: UserBase = Depends(get_current_user()),
    search_condition_service: SearchConditionService = Depends(
        get_search_condition_service
    ),
):
    return search_condition_service.update_search_condition(
        search_condition_id, current_user, request
    )


@router.post("/{search_condition_id}/duplicate", response_model=SearchConditionBase)
def duplicate_search_condition(
    search_condition_id: int,
    current_user: UserBase = Depends(get_current_user()),
    search_condition_service: SearchConditionService = Depends(
        get_search_condition_service
    ),
):
    return search_condition_service.duplicate_search_condition(
        search_condition_id, current_user
    )


@router.post("/refine-query", response_model=RefineQueryResponse)
def refine_query(
    request: RefineQueryRequest,
    current_user: UserBase = Depends(get_current_user()),
    search_condition_service: SearchConditionService = Depends(
        get_search_condition_service
    ),
):
    return search_condition_service.refine_query(request, current_user)
