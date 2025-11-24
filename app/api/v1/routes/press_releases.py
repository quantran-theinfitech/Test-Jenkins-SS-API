from typing import List, Optional

from elasticsearch import Elasticsearch
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

import app.api.v1.services.press_releases as press_release_service
from app.api.base.deps import get_es, get_session
from app.api.v1.dependencies import (
    get_current_user,
    get_plan_code,
    get_press_release_service,
)
from app.api.v1.dependencies.services import get_cross_search_service
from app.api.v1.schemas.press_releases import (
    ListingPRbusinessCategoryByIdsResponse,
    ListingPRbusinessCategoryQueryParams,
    ListingPRbusinessCategoryResponse,
    ListingPressReleasesResponse,
    PressReleaseBase,
)
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.search_press_releases import SearchPressReleaseResponse
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.cross_search_service import CrossSearchService, SearchTarget
from app.api.v1.services.press_release_service import PressReleaseService
from app.models.team import PlanCode

router = APIRouter()


@router.get("", response_model=ListingPressReleasesResponse)
def listing_press_releases(
    corporate_number: str,
    per_page: Optional[int] = Query(default=10, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    press_release_service: PressReleaseService = Depends(get_press_release_service),
):
    press_releases = press_release_service.listing_press_releases(
        corporate_number, per_page, page
    )
    total = press_release_service.get_press_releases_count(corporate_number)
    return ListingPressReleasesResponse(
        page=page, per_page=per_page, total=total, data=press_releases
    )


@router.get("/listing_by_url", response_model=List[PressReleaseBase])
def liting_press_releases_by_domain(
    url: str = Query(default=None),
    current_user: UserBase = Depends(get_current_user()),
    press_release_service: PressReleaseService = Depends(get_press_release_service),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return press_release_service.listing_press_releases_by_domain(
        url, listing_plan_code
    )


@router.post("/search", response_model=SearchPressReleaseResponse)
def search_press_release(
    search_condition: SearchCrossRequest,
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
    current_user: UserBase = Depends(get_current_user()),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    data, total, unlimited_total = press_release_service.search_press_releases(
        db, search_condition, es_client, page, per_page, listing_plan_code, current_user
    )
    return SearchPressReleaseResponse(
        page=page,
        per_page=per_page,
        total=total,
        unlimited_total=unlimited_total,
        data=data,
    )


@router.get("/business-categories", response_model=ListingPRbusinessCategoryResponse)
def listing_press_release_business_category(
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    request: ListingPRbusinessCategoryQueryParams = Depends(
        ListingPRbusinessCategoryQueryParams
    ),
):
    data, total = press_release_service.listing_press_release_business_category(
        db, request
    )
    return ListingPRbusinessCategoryResponse(
        data=data,
        total=total,
        page=request.page,
        per_page=request.per_page,
    )


@router.get(
    "/business-categories/search-by-ids",
    response_model=ListingPRbusinessCategoryByIdsResponse,
)
def listing_press_release_business_category_by_ids(
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    ids: List[int] = Query(default=[]),
):
    data = press_release_service.listing_press_release_business_category_by_ids(db, ids)
    return ListingPRbusinessCategoryByIdsResponse(data=data)


@router.post("/cross-search")
async def cross_search(
    request: Optional[SearchCrossRequest] = SearchCrossRequest(),
    current_user: UserBase = Depends(get_current_user()),
    cross_search_service: CrossSearchService = Depends(get_cross_search_service),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
):
    data, total, unlimited_total = await cross_search_service.search(
        request=request,
        target=SearchTarget.PRESS_RELEASE,
        current_user=current_user,
        page=page,
        per_page=per_page,
        listing_plan_code=listing_plan_code,
    )
    return SearchPressReleaseResponse(
        page=page,
        per_page=per_page,
        total=total,
        unlimited_total=unlimited_total,
        data=data,
    )
