from typing import Optional

from elasticsearch import Elasticsearch
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

import app.api.v1.services.integration.salesforce as salesforce_service
from app.api.base.deps import custom_generate_unique_id, get_es, get_session
from app.api.v1.dependencies.authentication import get_current_user
from app.api.v1.dependencies.credit import get_plan_code
from app.api.v1.schemas.hubspot_connections import SaleSmartCompanySchemaResponse
from app.api.v1.schemas.integration.salesforce import (
    ListingSalesforceCompaniesResponse,
    ListingSalesforcePullErrorLogsResponse,
    ListingSalesforcePullPersonErrorLogsResponse,
    ListingSalesforcePushErrorLogsResponse,
    ListingSalesforceSyncLogsResponse,
    SalesforceCreateCompanyRequest,
    SalesforceCreateCustomFieldRequest,
    SalesforceIntegrationDetailResponse,
    SalesforceIntegrationResponse,
    SalesforceListingCompnaySchemaResponse,
    SalesforceListingFieldMappingResponse,
    SalesforceManualPushCompanyRequest,
    SalesforceMarkDoneErrorLogRequest,
    SalesforceMatchCompanyRequest,
    SalesforcePullErrorLogDetailResponse,
    SalesforcePullPersonErrorLogDetailResponse,
    SalesforcePushErrorLogDetailResponse,
    SalesforceStateAutoBatchRequest,
    SalesforceStateAutoBatchResponse,
    SalesforceStaticErrorLogResponse,
    SalesforceSyncedCompanyResponse,
    SalesforceUpdateMappingFieldRequest,
)
from app.api.v1.schemas.users import UserBase
from app.models.team import PlanCode

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/connection", response_model=SalesforceIntegrationResponse)
def create_salesforce_connection(
    code: str = Query(default=""),
    is_reconnect: Optional[bool] = Query(default=False),
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.create_salesforce_integration(
        code, is_reconnect, db, current_user
    )


@router.patch("/connection", response_model=SalesforceIntegrationResponse)
def disconnect_salesforce_connection(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.disconnect_salesforce_integration(db, current_user)


@router.get("/connection-detail", response_model=SalesforceIntegrationDetailResponse)
def get_connection_detail(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.get_salesforce_integration_detail(db, current_user)


@router.get(
    "/listing-field-mappings", response_model=SalesforceListingFieldMappingResponse
)
def listing_salesforce_field_mappings(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.listing_salesforce_field_mappings(db, current_user)


@router.get(
    "/listing-salesmart-company-schema", response_model=SaleSmartCompanySchemaResponse
)
def listing_salesmart_schema(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.listing_salesmart_company_schema(db, current_user)


@router.get(
    "/listing-salesforce-company-schema",
    response_model=SalesforceListingCompnaySchemaResponse,
)
def listing_salesforce_schema(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.listing_salesforce_company_schema(db, current_user)


@router.put("/update-mapping-field", response_model=bool)
def update_mapping_salesforce_field(
    request: SalesforceUpdateMappingFieldRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.update_mapping_salesforce_field(db, current_user, request)


@router.get(
    "/listing-salesforce-sync-logs", response_model=ListingSalesforceSyncLogsResponse
)
def listing_salesforce_sync_logs(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    page: Optional[int] = None,
    per_page: Optional[int] = None,
):
    return salesforce_service.listing_salesforce_sync_logs(
        db=db, current_user=current_user, page=page, per_page=per_page
    )


@router.post("/push-companies")
def salesforce_manual_push_companies(
    request: SalesforceManualPushCompanyRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return salesforce_service.salesforce_manual_push_companies(
        db, current_user, request, listing_plan_code
    )


@router.post("/trigger-pull-companies")
def salesforce_trigger_pull_companies(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.salesforce_trigger_pull_companies(
        db,
        current_user,
    )


@router.post("/trigger-sync-affiliated-companies")
def salesforce_trigger_sync_affiliated_companies(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.salesforce_trigger_sync_affiliated_companies(
        db,
        current_user,
    )


@router.post("/trigger-pull-persons")
def salesforce_trigger_pull_persons(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.salesforce_trigger_pull_persons(
        db,
        current_user,
    )


@router.get(
    "/listing-salesforce-push-error-logs",
    response_model=ListingSalesforcePushErrorLogsResponse,
)
def listing_salesforce_push_error_logs(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    per_page: Optional[int] = Query(default=10, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return salesforce_service.listing_salesforce_push_error_logs(
        current_user=current_user,
        listing_plan_code=listing_plan_code,
        per_page=per_page,
        page=page,
        db=db,
    )


@router.get(
    "/listing-salesforce-pull-error-logs",
    response_model=ListingSalesforcePullErrorLogsResponse,
)
def listing_salesforce_pull_error_logs(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    per_page: Optional[int] = Query(default=10, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
):
    return salesforce_service.listing_salesforce_pull_error_logs(
        current_user=current_user,
        per_page=per_page,
        page=page,
        db=db,
    )


@router.get(
    "/listing-salesforce-pull-person-error-logs",
    response_model=ListingSalesforcePullPersonErrorLogsResponse,
)
def listing_salesforce_pull_person_error_logs(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    per_page: Optional[int] = Query(default=10, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
):
    return salesforce_service.listing_salesforce_pull_person_error_logs(
        current_user=current_user,
        per_page=per_page,
        page=page,
        db=db,
    )


@router.get(
    "/listing-salesforce-push-error-logs/{error_log_id}",
    response_model=SalesforcePushErrorLogDetailResponse,
)
def listing_salesforce_push_error_log_detail(
    error_log_id: int,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return salesforce_service.listing_salesforce_push_error_log_detail(
        current_user=current_user,
        listing_plan_code=listing_plan_code,
        error_log_id=error_log_id,
        db=db,
    )


@router.get(
    "/listing-salesforce-pull-error-logs/{error_log_id}",
    response_model=SalesforcePullErrorLogDetailResponse,
)
def listing_salesforce_pull_error_log_detail(
    error_log_id: int,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return salesforce_service.listing_salesforce_pull_error_log_detail(
        current_user=current_user,
        error_log_id=error_log_id,
        db=db,
        listing_plan_code=listing_plan_code,
    )


@router.get(
    "/listing-salesforce-pull-person-error-logs/{error_log_id}",
    response_model=SalesforcePullPersonErrorLogDetailResponse,
)
def listing_salesforce_pull_person_error_log_detail(
    error_log_id: int,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return salesforce_service.listing_salesforce_pull_person_error_log_detail(
        current_user=current_user,
        error_log_id=error_log_id,
        db=db,
        listing_plan_code=listing_plan_code,
    )


@router.get(
    "/search-companies-in-salesforce", response_model=ListingSalesforceCompaniesResponse
)
def search_companies_in_salesforce(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    keyword: str = Query(default=""),
):
    return salesforce_service.search_companies_in_salesforce(
        db=db,
        current_user=current_user,
        keyword=keyword,
    )


@router.post("/create-salesforce-company/{error_log_id}")
def create_salesforce_company(
    error_log_id: int,
    request: SalesforceCreateCompanyRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.create_salesforce_company(
        db=db,
        current_user=current_user,
        error_log_id=error_log_id,
        request=request,
    )


@router.post("/match-salesforce-company/{error_log_id}")
def match_salesforce_company(
    error_log_id: int,
    request: SalesforceMatchCompanyRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    es_client: Elasticsearch = Depends(get_es),
):
    return salesforce_service.match_salesforce_company(
        db=db,
        current_user=current_user,
        error_log_id=error_log_id,
        request=request,
        es_client=es_client,
    )


@router.put("/mark-done-error-log")
def update_mark_done_salesforce_error_log(
    request: SalesforceMarkDoneErrorLogRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.update_mark_done_error_log(
        db=db,
        current_user=current_user,
        request=request,
    )


@router.get(
    "/listing-mapping-suggest-fields",
    response_model=SalesforceListingFieldMappingResponse,
)
def listing_salesforce_mapping_suggest_fields(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.listing_salesforce_mapping_suggest_fields(
        db, current_user
    )


@router.post("/create-suggest-field")
def create_suggest_field_salesforce(
    request: SalesforceCreateCustomFieldRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.create_suggest_field_salesforce(db, current_user, request)


@router.get(
    "/get-synced-company/{corporate_number}",
    response_model=SalesforceSyncedCompanyResponse,
)
def salesforce_get_synced_company(
    corporate_number: str,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.get_synced_company(db, current_user, corporate_number)


@router.delete("/delete-synced-company/{corporate_number}")
def salesforce_delete_synced_company(
    corporate_number: str,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.delete_synced_company(db, current_user, corporate_number)


@router.get("/statistic/error-log", response_model=SalesforceStaticErrorLogResponse)
def get_salesforce_error_log_count(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.get_error_log_count(db, current_user)


@router.get("/state-auto-batch", response_model=SalesforceStateAutoBatchResponse)
def get_salesforce_state_auto_batch(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.get_state_auto_batch(db, current_user)


@router.put("/state-auto-batch")
def update_salesforce_state_auto_batch(
    request: SalesforceStateAutoBatchRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return salesforce_service.update_state_auto_batch(db, current_user, request)
