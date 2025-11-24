from typing import List, Literal, Optional

from elasticsearch import Elasticsearch
from fastapi import APIRouter, BackgroundTasks, Depends, Query, UploadFile
from sqlmodel import Session

import app.api.v1.services.collections as collection_service
from app.api.base.deps import custom_generate_unique_id, get_es, get_session
from app.api.v1.dependencies import get_current_user
from app.api.v1.dependencies.credit import get_plan_code
from app.api.v1.schemas.collections import (
    AddCollectionItemByCSVResponse,
    AddCollectionItemsByCSVRequest,
    AddCollectionItemsRequest,
    CheckCSVCollectionResponse,
    CompanyCollection,
    CreateCollectionRequest,
    GetCollectionDetailResponse,
    GetDraftCollectionDetailResponse,
    ListingCollectionsResponse,
    UpdateCollectionRequest,
)
from app.api.v1.schemas.companies import GetCollectionCompanyResponse
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase
from app.models import Company
from app.models.company_collection import StatusCode, TypeCode
from app.models.team import PlanCode

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.post("", response_model=int)
def create_collection(
    request_body: CreateCollectionRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return collection_service.create_collection(db, request_body, current_user)


@router.post("/create-by-csv", response_model=CheckCSVCollectionResponse)
def create_collection_company_by_csv(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    df = collection_service.check_csv_collection_service(file)

    company_collection = (
        collection_service.create_company_collection_when_uploading_csv(
            db, file.filename, current_user
        )
    )

    background_tasks.add_task(
        collection_service.create_company_collection_items_by_csv,
        db,
        df,
        company_collection,
        current_user,
    )

    return CheckCSVCollectionResponse(collection_id=company_collection.id)


@router.patch("/{collection_id}", response_model=CompanyCollection)
def update_collection(
    collection_id: int,
    request: UpdateCollectionRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return collection_service.update_collection(
        db, collection_id, current_user, request
    )


@router.get("/{collection_id}/companies", response_model=GetCollectionCompanyResponse)
def listing_collection_companies(
    collection_id: int,
    exclude_collection_id: Optional[int] = None,
    current_user: UserBase = Depends(get_current_user()),
    keyword: Optional[str] = None,
    per_page: Optional[int] = Query(default=10, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    order_by: Optional[Literal[tuple(Company.__fields__.keys())]] = "id",
    order_by_desc_flag: Optional[bool] = False,
    contact_form_url_flag: Optional[bool] = False,
    contact_email_flag: Optional[bool] = False,
    db: Session = Depends(get_session),
):
    companies, type_code_csv = collection_service.get_collection_companies(
        db,
        collection_id,
        exclude_collection_id,
        current_user.team_id,
        keyword,
        per_page,
        page,
        order_by,
        order_by_desc_flag,
        contact_form_url_flag,
        contact_email_flag,
    )

    total = collection_service.get_collection_companies_count(
        db,
        collection_id,
        exclude_collection_id,
        current_user.team_id,
        keyword,
        contact_form_url_flag,
        contact_email_flag,
        type_code_csv,
    )

    return GetCollectionCompanyResponse(
        page=page, per_page=per_page, total=total, data=companies
    )


@router.get("/{collection_id}", response_model=GetCollectionDetailResponse)
def get_collection_detail(
    collection_id: int,
    exclude_collection_id: Optional[int] = None,
    current_user: UserBase = Depends(get_current_user()),
    contact_form_url_flag: Optional[bool] = False,
    contact_email_flag: Optional[bool] = False,
    db: Session = Depends(get_session),
):
    return collection_service.get_collection_detail(
        db,
        collection_id,
        current_user,
        exclude_collection_id,
        contact_form_url_flag,
        contact_email_flag,
    )


@router.get("/draft/{collection_id}", response_model=GetDraftCollectionDetailResponse)
def get_draft_collection_detail(
    collection_id: int,
    current_user: UserBase = Depends(get_current_user()),
    contact_form_url_flag: Optional[bool] = False,
    db: Session = Depends(get_session),
):
    return collection_service.get_draft_collection_detail(
        db, collection_id, current_user, contact_form_url_flag
    )


@router.post("/count-items", response_model=int)
def get_collection_items_count(
    request_body: SearchCrossRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
):
    return collection_service.estimate_collection_items(
        db, request_body, current_user, es_client
    )


@router.get("", response_model=ListingCollectionsResponse)
def listing_all_collections(
    status_code: Optional[StatusCode] = None,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
    type_code: Optional[TypeCode] = None,
    keyword: Optional[str] = Query(default=None),
    group_id: Optional[int] = None,
    user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    collections = collection_service.get_all_collections(
        db, user, status_code, page, per_page, keyword, group_id, type_code
    )
    total = collection_service.get_all_collections_count(
        db, user, status_code, keyword, group_id, type_code
    )
    return ListingCollectionsResponse(
        page=page, per_page=per_page, total=total, data=collections
    )


@router.delete("/{collection_id}", response_model=int)
def delete_collection(
    collection_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return collection_service.delete_collection(db, collection_id, current_user)


@router.post("/collection/add-item", response_model=List[int])
def add_item_to_collection(
    request: AddCollectionItemsRequest,
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return collection_service.save_collection_items(
        db, request, current_user, listing_plan_code
    )


@router.post(
    "/collection/add-item-by-csv", response_model=AddCollectionItemByCSVResponse
)
def add_company_item_to_collection_by_csv(
    request: AddCollectionItemsByCSVRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    collection_ids = collection_service.add_item_collection_by_csv_service(
        db, request, current_user
    )

    return AddCollectionItemByCSVResponse(collection_ids=collection_ids)
