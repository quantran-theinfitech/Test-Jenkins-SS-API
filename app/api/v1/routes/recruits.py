from typing import List, Optional

from elasticsearch import Elasticsearch
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

import app.api.v1.services.recruits as recruits_service
from app.api.base.deps import custom_generate_unique_id, get_es, get_session
from app.api.v1.dependencies import get_current_user, get_plan_code
from app.api.v1.dependencies.services import get_cross_search_service
from app.api.v1.schemas.recruits import GetCompanyRecruitResponse, RecruitBase
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.search_recruits import SearchRecruitResponse
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.cross_search_service import CrossSearchService, SearchTarget
from app.api.v1.services.recruits import listing_recruit_by_domain_service
from app.models.team import PlanCode

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/", response_model=GetCompanyRecruitResponse)
def listing_company_recruits(
    corporate_number: str,
    db: Session = Depends(get_session),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
):
    recruits = recruits_service.listing_company_recruits(
        db, corporate_number, per_page, page
    )
    total = recruits_service.listing_company_recruits_count(db, corporate_number)
    return GetCompanyRecruitResponse(
        page=page, per_page=per_page, data=recruits, total=total
    )


@router.get("/listing_by_url", response_model=List[RecruitBase])
def listing_recruit_by_domain(
    db: Session = Depends(get_session),
    url: str = Query(default=None),
    current_user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return listing_recruit_by_domain_service.listing_recruit_by_domain(
        db, url, listing_plan_code
    )


@router.get("/{recruit_id}", response_model=RecruitBase)
def get_company_recruit_detail(
    recruit_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    recruit_detail = recruits_service.get_company_recruit_detail(
        db, current_user, listing_plan_code, recruit_id
    )
    return recruit_detail


@router.post("/search", response_model=SearchRecruitResponse)
def search_recruits(
    search_condition: SearchCrossRequest,
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
    current_user: UserBase = Depends(get_current_user()),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    data, total, unlimited_total = recruits_service.search_recruits(
        db, search_condition, es_client, page, per_page, listing_plan_code, current_user
    )
    return SearchRecruitResponse(
        page=page,
        per_page=per_page,
        total=total,
        unlimited_total=unlimited_total,
        data=data,
    )


@router.post("/cross-search", response_model=SearchRecruitResponse)
async def cross_search_recruit(
    search_condition: SearchCrossRequest,
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
    current_user: UserBase = Depends(get_current_user()),
    cross_search_service: CrossSearchService = Depends(get_cross_search_service),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    data, total, unlimited_total = await cross_search_service.search(
        search_condition,
        SearchTarget.RECRUIT,
        current_user,
        page,
        per_page,
        listing_plan_code,
    )
    return SearchRecruitResponse(
        page=page,
        per_page=per_page,
        total=total,
        unlimited_total=unlimited_total,
        data=data,
    )
