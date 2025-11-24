from typing import List, Literal, Optional

from elasticsearch import Elasticsearch
from fastapi import APIRouter, BackgroundTasks, Depends, Query, UploadFile
from sqlmodel import Session

import app.api.v1.services.person_collections as person_collection_service
import app.api.v1.services.person_collections as collection_service
from app.api.base.deps import custom_generate_unique_id, get_es, get_session
from app.api.v1.dependencies import get_current_user, get_plan_code
from app.api.v1.schemas.collections import (
    AddCollectionItemByCSVResponse,
    AddCollectionItemsByCSVRequest,
    CheckCSVCollectionResponse,
)
from app.api.v1.schemas.person_collections import (
    AddPersonCollectionItemsRequest,
    CreatePersonCollectionRequest,
    ListingCollectionDetailResponse,
    ListingPersonCollectionResponse,
    PersonCollectionBase,
    PersonCollectionResponse,
    UpdatePersonCollectionRequest,
)
from app.api.v1.schemas.search_cross import SearchCrossRequest
from app.api.v1.schemas.users import UserBase
from app.models.person import Person
from app.models.person_collection import StatusCode, TypeCode
from app.models.team import PlanCode

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("", response_model=ListingPersonCollectionResponse)
def listing_person_collections(
    db: Session = Depends(get_session),
    per_page: Optional[int] = None,
    page: Optional[int] = None,
    type_code: Optional[TypeCode] = None,
    user: UserBase = Depends(get_current_user()),
    keyword: Optional[str] = Query(default=None),
    status_code: Optional[StatusCode] = None,
    group_id: Optional[int] = None,
):
    collections = person_collection_service.listing_person_collections(
        db, page, per_page, user, keyword, status_code, group_id, type_code
    )
    count_collections = person_collection_service.count_person_collections(
        db, user, keyword, status_code, group_id, type_code
    )
    return ListingPersonCollectionResponse(
        page=page, per_page=per_page, total=count_collections, data=collections
    )


@router.post("/create-by-csv", response_model=CheckCSVCollectionResponse)
def create_collection_person_by_csv(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    df = collection_service.check_csv_collection_service(file)

    person_collection = collection_service.create_person_collection_when_uploading_csv(
        db, file.filename, current_user
    )

    background_tasks.add_task(
        collection_service.create_person_collection_items_by_csv,
        db,
        df,
        person_collection,
        current_user,
    )

    return CheckCSVCollectionResponse(collection_id=person_collection.id)


@router.post("/statistics/by-condition", response_model=int)
def statistics_by_condition(
    request_body: SearchCrossRequest,
    current_user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
):
    return person_collection_service.statistics_by_condition(
        db, request_body, current_user, listing_plan_code, es_client
    )


@router.post("/persons", response_model=int)
def create_person_collection(
    request_body: CreatePersonCollectionRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return person_collection_service.create_person_collections(
        request_body, db, current_user
    )


@router.get("/{collection_id}", response_model=PersonCollectionBase)
def get_person_collection_detail(
    collection_id: int,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return person_collection_service.get_collection_detail(
        db, collection_id, current_user
    )


@router.get("/{collection_id}/persons", response_model=ListingCollectionDetailResponse)
def get_collection_persons(
    collection_id: int,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    page: Optional[int] = Query(default=1, ge=1),
    per_page: Optional[int] = Query(default=5, ge=1),
    keyword: Optional[str] = None,
    order_by: Optional[Literal[tuple(Person.__fields__.keys())]] = "id",
    order_by_desc_flag: Optional[bool] = False,
):
    listing_collection_detail = person_collection_service.get_collection_persons(
        collection_id,
        current_user.team_id,
        db,
        page,
        per_page,
        keyword,
        order_by,
        order_by_desc_flag,
    )
    count_listing_collection_detail = (
        person_collection_service.count_get_collection_persons(
            collection_id, current_user.team_id, db, keyword
        )
    )
    return ListingCollectionDetailResponse(
        page=page,
        per_page=per_page,
        total=count_listing_collection_detail,
        data=listing_collection_detail,
    )


@router.patch("/{collection_id}", response_model=PersonCollectionResponse)
def update_person_collection(
    collection_id: int,
    request: UpdatePersonCollectionRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return person_collection_service.update_person_collection(
        db, collection_id, current_user, request
    )


@router.delete("/{collection_id}", response_model=int)
def delete_person_collection(
    collection_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return person_collection_service.delete_person_collection(
        db, collection_id, current_user
    )


@router.post("/person-collection/add-item", response_model=List[int])
def add_person_item_to_collection(
    request: AddPersonCollectionItemsRequest,
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return person_collection_service.save_person_collection_items(
        db, request, current_user, listing_plan_code
    )


@router.post(
    "/collection/add-item-by-csv", response_model=AddCollectionItemByCSVResponse
)
def add_person_item_to_collection_by_csv(
    request: AddCollectionItemsByCSVRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    collection_ids = collection_service.add_person_item_collection_by_csv_service(
        db, request, current_user
    )

    return AddCollectionItemByCSVResponse(collection_ids=collection_ids)
