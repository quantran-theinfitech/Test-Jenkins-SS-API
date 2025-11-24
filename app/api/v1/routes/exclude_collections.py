from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, UploadFile
from sqlmodel import Session

import app.api.v1.services.exclude_collections as exclude_collection_service
from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user, has_paid_plan
from app.api.v1.schemas.exclude_collections import (
    CreateCompanyExcludeCollectionRequest,
    ExcludeCollectionCompaniesResponse,
    ExcludeCollectionDetailResponse,
    ListingCompanyExcludeCollectionResponse,
)
from app.api.v1.schemas.users import UserBase
from app.models.company_exclude_collection import TypeCode
from app.models.team import PlanCode
from app.models.user import User

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("", response_model=ListingCompanyExcludeCollectionResponse)
def listing_all_exclude_collections(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user()),
    keyword: Optional[str] = Query(default=None),
    page: Optional[int] = None,
    per_page: Optional[int] = None,
):
    collections = exclude_collection_service.listing_all_exclude_collections(
        db, current_user, keyword, page, per_page
    )

    total = exclude_collection_service.count_listing_all_exclude_collections(
        db,
        current_user,
        keyword,
    )
    return ListingCompanyExcludeCollectionResponse(
        per_page=per_page,
        current_page=page,
        total=total,
        data=collections,
    )


@router.get(
    "/{exclude_id}/companies", response_model=ExcludeCollectionCompaniesResponse
)
def listing_exclude_collection_companies(
    exclude_id: int,
    current_user: User = Depends(get_current_user()),
    keyword: Optional[str] = None,
    per_page: Optional[int] = Query(default=10, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    db: Session = Depends(get_session),
):
    companies = exclude_collection_service.listing_exclude_collection_companies(
        exclude_id, current_user.team_id, keyword, db, page, per_page
    )
    total = exclude_collection_service.get_exclude_collection_companies_count(
        db, exclude_id, current_user.team_id, keyword
    )
    return ExcludeCollectionCompaniesResponse(
        page=page, per_page=per_page, total=total, data=companies
    )


@router.get("/{exclude_collection_id}", response_model=ExcludeCollectionDetailResponse)
def get_exclude_collection_detail(
    exclude_collection_id: int,
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return exclude_collection_service.get_exclude_collection_detail(
        db, exclude_collection_id, current_user.team_id
    )


@router.post("", response_model=int)
def create_exclude_collection_companies(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    request: CreateCompanyExcludeCollectionRequest = Depends(),
    listing_plan_code: PlanCode = Depends(has_paid_plan()),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    df = exclude_collection_service.read_exclude_collection_csv(file)
    exclude_collection = exclude_collection_service.create_exclude_collection(
        db, request, current_user, TypeCode.CSV
    )
    background_tasks.add_task(
        exclude_collection_service.create_company_exclude_collection_items_by_csv,
        db,
        exclude_collection,
        df,
        current_user,
    )
    return exclude_collection.id


@router.post("/create-by-corporate-numbers", response_model=int)
def create_exclude_collection_companies_by_corporate_numbers(
    request: CreateCompanyExcludeCollectionRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    exclude_collection = exclude_collection_service.create_exclude_collection(
        db, request, current_user, TypeCode.SYS
    )

    exclude_collection_service.create_exclude_collection_by_corporate_numbers(
        db, request.corporate_numbers, exclude_collection
    )

    return exclude_collection.id
