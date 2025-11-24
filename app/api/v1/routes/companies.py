from typing import List, Optional

from elasticsearch import Elasticsearch
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session

import app.api.v1.services.companies as company_service
from app.api.base.deps import custom_generate_unique_id, get_es, get_session
from app.api.v1.dependencies import get_current_user, get_plan_code
from app.api.v1.dependencies.services import get_cross_search_service
from app.api.v1.schemas.companies import (
    CompanyActivitiesResponse,
    CompanyBase,
    CompanyByKeywordResponse,
    CompanyDetailResponse,
    CompanyDetailStatisticTotalResponse,
    CompanyTechnologyResponse,
    DownloadCompanyConditionRequest,
    DownloadCompanyRequest,
    GetCompanyActivitesRequest,
    ListingCompanyStatisticResponse,
    UpdateTeamCompanyRequest,
    UpdateTeamCompanyResponse,
)
from app.api.v1.schemas.search_companies import (
    GetListCorporateNumbers,
    GetTotalCompanyLockAndUnlockResponse,
    SearchCompanyByTeamIdResponse,
    SearchCompanyResponse,
)
from app.api.v1.schemas.search_cross import (
    DowloadCsvRequest,
    GetIDsByTotalSelect,
    ListCorporateNumber,
    SearchCrossRequest,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.companies.download_companies_csv_service import (
    check_credit_download_companies,
)
from app.api.v1.services.companies.listing_companies_corporate_number_by_select import (
    get_total_lock_unlock_companies_service,
    listing_companies_corporate_number_by_select,
)
from app.api.v1.services.cross_search_service import CrossSearchService, SearchTarget
from app.models.company_bookmark import CompanyBookmark
from app.models.team import PlanCode
from utils.extract_domain import (
    normalized_domain_search_companies,
    normalized_sns_url_search_persons,
)

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.post("/download", response_model=List[str])
def download_companies(
    request_body: DownloadCompanyRequest,
    es_client: Elasticsearch = Depends(get_es),
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return company_service.download_companies(
        db, es_client, current_user, request_body.corporate_numbers
    )


@router.post("/download-all", response_model=int)
def download_all_companies(
    request_body: DownloadCompanyConditionRequest,
    es_client: Elasticsearch = Depends(get_es),
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return company_service.download_all_companies(
        db, es_client, current_user, request_body.search_condition, request_body.mode
    )


@router.post("/{company_id}/bookmark", response_model=CompanyBookmark)
def create_bookmark(
    company_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return company_service.bookmark_company(db, company_id, current_user)


@router.delete("/{company_id}/bookmark", response_model=CompanyBookmark)
def delete_bookmark(
    company_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return company_service.un_bookmark_company(db, company_id, current_user)


@router.post("/search", response_model=SearchCompanyResponse)
def search_companies(
    search_condition: Optional[SearchCrossRequest] = SearchCrossRequest(),
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    current_user: UserBase = Depends(get_current_user()),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
):
    data, total, unlimited_total = company_service.search_companies(
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
    return SearchCompanyResponse(
        page=page,
        per_page=per_page,
        total=total,
        unlimited_total=unlimited_total,
        data=data,
    )


@router.post("/get-list-corporate-numbers", response_model=GetListCorporateNumbers)
def get_list_corporate_number(
    request: GetIDsByTotalSelect,
    search_condition: Optional[SearchCrossRequest] = SearchCrossRequest(),
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
    current_user: UserBase = Depends(get_current_user()),
):
    list_corporate_number = listing_companies_corporate_number_by_select(
        db,
        normalized_sns_url_search_persons(
            normalized_domain_search_companies(search_condition)
        ),
        es_client,
        1,
        request.total_select,
        current_user,
    )

    return GetListCorporateNumbers(corporate_numbers=list_corporate_number)


@router.post(
    "/get-total-lock-unlock", response_model=GetTotalCompanyLockAndUnlockResponse
)
def get_total_lock_unlock_companies(
    request: ListCorporateNumber,
    db: Session = Depends(get_session),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    current_user: UserBase = Depends(get_current_user()),
):
    data = get_total_lock_unlock_companies_service(
        db, request.corporate_numbers, listing_plan_code, current_user
    )

    return data


@router.patch("/{corporate_number}", response_model=UpdateTeamCompanyResponse)
def update_team_company(
    corporate_number: str,
    request: UpdateTeamCompanyRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return company_service.update_team_company(
        db,
        corporate_number,
        request,
        current_user,
        listing_plan_code,
    )


@router.post("/statistics", response_model=ListingCompanyStatisticResponse)
def listing_companies_statistics(
    search_condition: Optional[SearchCrossRequest] = None,
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
    current_user: UserBase = Depends(get_current_user()),
):
    return company_service.listing_companies_statistics(
        db,
        normalized_sns_url_search_persons(
            normalized_domain_search_companies(search_condition)
        ),
        es_client,
        current_user,
    )


@router.get("/listing", response_model=List[CompanyBase])
def listing_companies_by_ids(
    corporate_numbers: List[str] = Query(..., min_items=1, max_items=10000),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return company_service.listing_companies_by_ids(
        db, corporate_numbers, current_user, listing_plan_code
    )


@router.get("/get_by_domain", response_model=CompanyBase)
def get_company_by_domain(
    db: Session = Depends(get_session),
    url: str = Query(default=None),
    current_user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return company_service.get_company_by_domain(
        db, url, current_user, listing_plan_code
    )


@router.post("/listing-downloaded", response_model=SearchCompanyByTeamIdResponse)
def listing_companies_by_team_id(
    search_condition: Optional[SearchCrossRequest] = SearchCrossRequest(),
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
    current_user: UserBase = Depends(get_current_user()),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
):
    data, total, unlimited_total = company_service.listing_companies_by_team_id(
        db,
        normalized_domain_search_companies(search_condition),
        es_client,
        page,
        per_page,
        current_user,
    )

    return SearchCompanyByTeamIdResponse(
        page=page,
        per_page=per_page,
        total=total,
        unlimited_total=unlimited_total,
        data=data,
    )


@router.get("/tag", response_model=List[str])
def search_tag_team_company(
    tag: str = Query(default=""),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return company_service.search_tag_team_company(tag, db, current_user)


@router.get("/original_tags", response_model=List[str])
def search_original_tag_team_company(
    tag: str = Query(default=""),
    es_client: Elasticsearch = Depends(get_es),
    per_page: Optional[int] = Query(default=30),
    page: Optional[int] = Query(default=1),
):
    return company_service.search_original_tag_team_company(
        tag, es_client, per_page, page
    )


@router.get("/{corporate_number}", response_model=CompanyDetailResponse)
def get_company_detail(
    corporate_number: str,
    db: Session = Depends(get_session),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    current_user: UserBase = Depends(get_current_user()),
):
    return company_service.get_company_detail(
        db, corporate_number, current_user, listing_plan_code
    )


@router.get("/{corporate_number}/activities", response_model=CompanyActivitiesResponse)
def get_company_activities(
    corporate_number: str,
    per_page: Optional[int] = Query(default=5),
    page: Optional[int] = Query(default=1),
    db: Session = Depends(get_session),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    current_user: UserBase = Depends(get_current_user()),
):
    request = GetCompanyActivitesRequest(
        corporate_number=corporate_number, page=page, per_page=per_page
    )
    data = company_service.get_company_activities(
        db, request, current_user, listing_plan_code
    )
    return CompanyActivitiesResponse(data=data)


@router.get(
    "/{corporate_number}/technologies", response_model=CompanyTechnologyResponse
)
def get_company_technologies(
    corporate_number: str,
    is_limit: Optional[bool] = Query(default=False),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    data = company_service.get_company_technologies(db, corporate_number, is_limit)
    return CompanyTechnologyResponse(data=data)


@router.post("/download/csv", status_code=204)
def download_companies_csv(
    search_condition: DowloadCsvRequest,
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    list_company_corporate_numbers = search_condition.list_company_corporate_numbers
    if listing_plan_code is not PlanCode.UNLIMITED:
        _, list_company_corporate_numbers = check_credit_download_companies(
            db,
            current_user,
            search_condition.type_download,
            search_condition.list_company_corporate_numbers,
        )

    if len(list_company_corporate_numbers) < 500:
        return company_service.download_companies_csv(
            search_condition=search_condition,
            current_user=current_user,
            listing_plan_code=listing_plan_code,
            db=db,
        )

    background_tasks.add_task(
        company_service.download_companies_csv,
        search_condition,
        current_user,
        listing_plan_code,
        db,
        True,
    )


@router.get("/list/company", response_model=CompanyByKeywordResponse)
def search_company_by_keyword(
    db: Session = Depends(get_session),
    keyword: str = Query(default=""),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
    es_client: Elasticsearch = Depends(get_es),
    per_page: Optional[int] = Query(default=30),
    page: Optional[int] = Query(default=1),
):
    return company_service.get_company_by_keyword(
        db, keyword, listing_plan_code, es_client, per_page, page
    )


@router.post("/template-csv/download", response_class=StreamingResponse)
def download_companies_csv_template(
    user: UserBase = Depends(get_current_user()),
):
    return company_service.download_companies_csv_template()


@router.get(
    "/{corporate_number}/statistics/total",
    response_model=CompanyDetailStatisticTotalResponse,
)
def get_company_statistics_total(
    corporate_number: str,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return company_service.get_company_statistics_total(
        db=db, current_user=current_user, corporate_number=corporate_number
    )


@router.post("/cross-search", response_model=SearchCompanyResponse)
async def cross_search_company(
    search_condition: Optional[SearchCrossRequest] = None,
    current_user: UserBase = Depends(get_current_user()),
    cross_search_service: CrossSearchService = Depends(get_cross_search_service),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    data, total, unlimited_total = await cross_search_service.search(
        search_condition,
        SearchTarget.COMPANY,
        current_user,
        page,
        per_page,
        listing_plan_code,
    )
    return SearchCompanyResponse(
        page=page,
        per_page=per_page,
        total=total,
        unlimited_total=unlimited_total,
        data=data,
    )


@router.post("/cross-search/statistics", response_model=ListingCompanyStatisticResponse)
async def cross_search_companies_statistics(
    search_condition: Optional[SearchCrossRequest] = None,
    current_user: UserBase = Depends(get_current_user()),
    cross_search_service: CrossSearchService = Depends(get_cross_search_service),
):
    return await cross_search_service.statistics(
        request=search_condition,
        target=SearchTarget.COMPANY,
        current_user=current_user,
    )


@router.post(
    "/cross-search/corporate-number-list", response_model=GetListCorporateNumbers
)
def get_list_corporate_number_for_downloading(
    request: GetIDsByTotalSelect,
    search_condition: Optional[SearchCrossRequest] = None,
    cross_search_service: CrossSearchService = Depends(get_cross_search_service),
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
    current_user: UserBase = Depends(get_current_user()),
    page: Optional[int] = Query(default=1, ge=1),
    per_page: Optional[int] = Query(default=20, ge=1),
):
    list_corporate_number = (
        cross_search_service.listing_companies_corporate_number_by_select(
            db,
            search_condition,
            es_client,
            page,
            per_page,
            request.total_select,
            current_user,
        )
    )

    return GetListCorporateNumbers(corporate_numbers=list_corporate_number)
