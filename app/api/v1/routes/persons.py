from typing import List, Optional

from elasticsearch import Elasticsearch
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session

import app.api.v1.services.persons as person_service
from app.api.base.deps import custom_generate_unique_id, get_es, get_session
from app.api.v1.dependencies import get_current_user, get_plan_code
from app.api.v1.dependencies.services import get_cross_search_service
from app.api.v1.schemas.person_careers import ListingPersonCareerResponse
from app.api.v1.schemas.person_educations import ListingPersonEducaionResponse
from app.api.v1.schemas.persons import (
    DownloadPersonConditionRequest,
    DownloadPersonRequest,
    ListingDownloadedKeymansResponse,
    PersonDetailResponse,
    PersonsStatisticsResponse,
    RoleGroupCode,
)
from app.api.v1.schemas.search_cross import (
    DowloadCsvRequest,
    GetIDsByTotalSelect,
    ListUUIDs,
    SearchCrossRequest,
)
from app.api.v1.schemas.search_persons import (
    GetListUUIDs,
    GetTotalPersonLockAndUnlockResponse,
    SearchPersonResponse,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.cross_search_service import CrossSearchService, SearchTarget
from app.api.v1.services.persons.download_persons_csv_service import (
    check_credit_download_person,
)
from app.api.v1.services.persons.listing_person_uuids_by_select import (
    get_total_lock_unlock_person_service,
)
from app.models.team import PlanCode
from utils.extract_domain import (
    normalized_domain_search_companies,
    normalized_sns_url_search_persons,
)

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.post("/", response_model=ListingDownloadedKeymansResponse)
def listing_downloaded_keymans(
    search_condition: Optional[SearchCrossRequest] = SearchCrossRequest(),
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
    current_user: UserBase = Depends(get_current_user()),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
):

    data, total, unlimited_total = person_service.listing_downloaded_keyman(
        db,
        normalized_sns_url_search_persons(
            normalized_domain_search_companies(search_condition)
        ),
        es_client,
        page,
        per_page,
        current_user,
    )
    return ListingDownloadedKeymansResponse(
        page=page,
        per_page=per_page,
        total=total,
        unlimited_total=unlimited_total,
        data=data,
    )


@router.post("/statistics", response_model=PersonsStatisticsResponse)
def statistics_persons(
    search_condition: SearchCrossRequest,
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
    current_user: UserBase = Depends(get_current_user()),
):
    return person_service.statistics_persons(
        normalized_sns_url_search_persons(
            normalized_domain_search_companies(search_condition)
        ),
        db,
        es_client,
        current_user,
    )


@router.get(
    "/listing-by-corporate_number/{corporate_number}",
    response_model=SearchPersonResponse,
)
def listing_person_by_corporate_number(
    corporate_number: str,
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
    user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    page: int = Query(default=1),
    per_page: int = Query(default=20),
    role_group_code: Optional[List[RoleGroupCode]] = Query(default=None),
):
    persons, total = person_service.listing_person_by_corporate_number(
        corporate_number,
        db,
        es_client,
        user,
        listing_plan_code,
        page,
        per_page,
        role_group_code,
    )

    return SearchPersonResponse(
        page=page,
        per_page=per_page,
        total=total,
        unlimited_total=total,
        data=persons,
    )


@router.get("/{person_uuid}/careers", response_model=ListingPersonCareerResponse)
def listing_person_careers(
    person_uuid: str,
    db: Session = Depends(get_session),
    user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    keyword: Optional[str] = Query(default=None),
    page: Optional[int] = None,
    per_page: Optional[int] = None,
):
    careers, count = person_service.listing_person_careers(
        person_uuid, db, user, listing_plan_code, keyword, page, per_page
    )
    return ListingPersonCareerResponse(
        page=page, per_page=per_page, total=count, data=careers
    )


@router.get("/{person_uuid}/educations", response_model=ListingPersonEducaionResponse)
def listing_person_educations(
    person_uuid: str,
    db: Session = Depends(get_session),
    user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    keyword: Optional[str] = Query(default=None),
    page: Optional[int] = None,
    per_page: Optional[int] = None,
):
    educations = person_service.listing_person_educations(
        person_uuid, db, user, listing_plan_code, keyword, page, per_page
    )
    count = person_service.count_person_educations(
        person_uuid, db, user, listing_plan_code, keyword
    )
    return ListingPersonEducaionResponse(
        page=page, per_page=per_page, total=count, data=educations
    )


@router.post("/search", response_model=SearchPersonResponse)
def search_persons(
    search_condition: Optional[SearchCrossRequest] = SearchCrossRequest(),
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
    current_user: UserBase = Depends(get_current_user()),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    data, total, unlimited_total = person_service.search_persons(
        db,
        normalized_sns_url_search_persons(
            normalized_domain_search_companies(search_condition)
        ),
        es_client,
        page,
        per_page,
        listing_plan_code,
        current_user,
    )
    return SearchPersonResponse(
        page=page,
        per_page=per_page,
        total=total,
        unlimited_total=unlimited_total,
        data=data,
    )


@router.post("/get-list-uuids", response_model=GetListUUIDs)
def get_list_uuids(
    request: GetIDsByTotalSelect,
    search_condition: Optional[SearchCrossRequest] = SearchCrossRequest(),
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
    current_user: UserBase = Depends(get_current_user()),
):
    list_uuids = person_service.listing_person_uuids_by_select(
        db,
        normalized_sns_url_search_persons(
            normalized_domain_search_companies(search_condition)
        ),
        es_client,
        1,
        request.total_select,
        current_user,
        request.max_person_by_company,
    )

    return GetListUUIDs(
        uuids=list_uuids,
    )


@router.post(
    "/get-total-lock-unlock", response_model=GetTotalPersonLockAndUnlockResponse
)
def get_total_lock_unlock_persons(
    request: ListUUIDs,
    db: Session = Depends(get_session),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    current_user: UserBase = Depends(get_current_user()),
):
    data = get_total_lock_unlock_person_service(
        db, request.uuids, listing_plan_code, current_user
    )

    return data


@router.post("/download", response_model=List[str])
def download_person(
    request_body: DownloadPersonRequest,
    es_client: Elasticsearch = Depends(get_es),
    current_user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    db: Session = Depends(get_session),
):
    return person_service.download_persons(
        db, es_client, current_user, listing_plan_code, request_body.person_uuids
    )


@router.post("/download-all", response_model=object)
def download_all_persons(
    request_body: DownloadPersonConditionRequest,
    es_client: Elasticsearch = Depends(get_es),
    current_user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    db: Session = Depends(get_session),
):
    return person_service.download_all_persons(
        db,
        es_client,
        current_user,
        listing_plan_code,
        request_body.search_condition,
        request_body.mode,
    )


@router.post("/download/csv", status_code=204)
def download_csv_persons(
    search_condition: DowloadCsvRequest,
    current_user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    db: Session = Depends(get_session),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    list_person_uuids = search_condition.list_person_uuids
    if listing_plan_code is not PlanCode.UNLIMITED:
        _, list_person_uuids = check_credit_download_person(
            db,
            current_user,
            search_condition.type_download,
            search_condition.list_person_uuids,
        )
    if len(list_person_uuids) < 500:
        return person_service.download_persons_csv(
            db,
            search_condition,
            current_user,
            listing_plan_code,
        )

    background_tasks.add_task(
        person_service.download_persons_csv,
        db,
        search_condition,
        current_user,
        listing_plan_code,
        True,
    )


@router.get("/{person_uuid}", response_model=PersonDetailResponse)
def get_person_detail(
    person_uuid: str,
    db: Session = Depends(get_session),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    current_user: UserBase = Depends(get_current_user()),
):
    return person_service.get_person_detail(
        db, person_uuid, current_user, listing_plan_code
    )


@router.post("/template-csv/download", response_class=StreamingResponse)
def download_persons_csv_template(
    user: UserBase = Depends(get_current_user()),
):
    return person_service.download_persons_csv_template()


@router.post("/cross-search", response_model=SearchPersonResponse)
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
        target=SearchTarget.PERSON,
        current_user=current_user,
        page=page,
        per_page=per_page,
        listing_plan_code=listing_plan_code,
    )
    return SearchPersonResponse(
        page=page,
        per_page=per_page,
        total=total,
        unlimited_total=unlimited_total,
        data=data,
    )


@router.post("/cross-search/statistics", response_model=PersonsStatisticsResponse)
async def cross_search_statistics(
    request: Optional[SearchCrossRequest] = SearchCrossRequest(),
    current_user: UserBase = Depends(get_current_user()),
    cross_search_service: CrossSearchService = Depends(get_cross_search_service),
):
    return await cross_search_service.statistics(
        request=request,
        target=SearchTarget.PERSON,
        current_user=current_user,
    )


@router.post("/cross-search/uuids", response_model=GetListUUIDs)
async def get_cross_search_list_uuids(
    request: GetIDsByTotalSelect,
    search_condition: Optional[SearchCrossRequest] = SearchCrossRequest(),
    cross_search_service: CrossSearchService = Depends(get_cross_search_service),
    current_user: UserBase = Depends(get_current_user()),
):
    list_uuids = await cross_search_service.get_list_person_uuids(
        normalized_sns_url_search_persons(
            normalized_domain_search_companies(search_condition)
        ),
        current_user,
        1,
        request.total_select,
        request.max_person_by_company,
    )

    return GetListUUIDs(
        uuids=list_uuids,
    )
