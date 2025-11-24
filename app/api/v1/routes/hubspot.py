from typing import Optional

from elasticsearch import Elasticsearch
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

import app.api.v1.services.hubspot_connections as hubspot_connection_service
from app.api.base.deps import custom_generate_unique_id, get_es, get_session
from app.api.v1.dependencies import get_current_user, get_plan_code
from app.api.v1.schemas.hubspot_connections import (
    CreateCompanyHubspotRequest,
    GetSyncedCompanyResponse,
    HubspotCompanySchemaResponse,
    HubspotConnectionDetailResponse,
    HubspotConnectionResponse,
    HubspotCreateFieldRequest,
    HubspotManualIdentifyLogsDetailResponse,
    HubspotManualPullLogsDetailResponse,
    HubspotManualPushCompanyRequest,
    HubspotManualPushLogsDetailResponse,
    HubspotMappingSettingResponse,
    HubspotStateAutoBatchRequest,
    HubspotStateAutoBatchResponse,
    HubspotStaticErrorLogResponse,
    ListingHubspotManualIdentifyLogs,
    ListingHubspotManualPullLogs,
    ListingHubspotManualPushLogs,
    ListingHubspotSyncLogs,
    MarkDoneErrorLogHubspotRequest,
    MatchCompanyHubspotRequest,
    SaleSmartCompanySchemaResponse,
    SearchCompanyHubspotResponse,
    UpdateMappingFieldRequest,
)
from app.api.v1.schemas.users import UserBase
from app.models.team import PlanCode

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/connection", response_model=HubspotConnectionResponse)
def create_hubspot_connection(
    code: str = Query(default=""),
    is_reconnect: Optional[bool] = Query(default=False),
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.create_hubspot_connection(
        code, is_reconnect, db, current_user
    )


@router.patch("/connection", response_model=int)
def disconnect_hubspot(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.disconnect_hubspot_connection(db, current_user)


@router.get("/connection-detail", response_model=HubspotConnectionDetailResponse)
def connection_detail(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.hubspot_connection_detail(db, current_user)


@router.get("/listing-mapping", response_model=HubspotMappingSettingResponse)
def listing_mapping(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.listing_mapping(db, current_user)


@router.get(
    "/listing-mapping-suggest-field", response_model=HubspotMappingSettingResponse
)
def listing_mapping_suggest_field(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.listing_mapping_suggest_field(db, current_user)


@router.post("/create-suggest-field-hubspot", response_model=int)
def create_suggest_field_hubspot(
    request: HubspotCreateFieldRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.create_hubspot_field(db, current_user, request)


@router.get("/listing-schema-hubspot", response_model=HubspotCompanySchemaResponse)
def listing_hubspot_company_schema(
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return hubspot_connection_service.listing_schema_company_hubspot(db, current_user)


@router.get("/listing-schema-sale-smart", response_model=SaleSmartCompanySchemaResponse)
def listing_sale_smart_schema(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.listing_schema_sale_smart(db, current_user)


@router.put("/update-mapping-hubspot", response_model=int)
def update_mapping_hubspot(
    request: UpdateMappingFieldRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.update_mapping_hubspot(db, current_user, request)


@router.get("/listing-hubspot-sync-log", response_model=ListingHubspotSyncLogs)
def listing_hubspot_sync_log(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    page: Optional[int] = None,
    per_page: Optional[int] = None,
):
    return hubspot_connection_service.listing_hubspot_sync_log(
        db=db, current_user=current_user, page=page, per_page=per_page
    )


@router.get(
    "/listing-hubspot-manual-push-log", response_model=ListingHubspotManualPushLogs
)
def listing_hubspot_manual_push_log(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    per_page: Optional[int] = Query(default=10, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return hubspot_connection_service.listing_hubspot_manual_push_log(
        db, listing_plan_code, current_user, per_page, page
    )


@router.get(
    "/listing-hubspot-manual-pull-log", response_model=ListingHubspotManualPullLogs
)
def listing_hubspot_manual_pull_log(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    per_page: Optional[int] = Query(default=10, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
):
    return hubspot_connection_service.listing_hubspot_manual_pull_log(
        db, current_user, per_page, page
    )


@router.get(
    "/listing-hubspot-manual-pull-log/{manual_log_id}",
    response_model=HubspotManualPullLogsDetailResponse,
)
def listing_hubspot_manual_pull_log_detail(
    manual_log_id: Optional[int],
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return hubspot_connection_service.hubspot_manual_pull_log_detail(
        manual_log_id, db, current_user, listing_plan_code
    )


@router.get(
    "/listing-hubspot-manual-push-log/{manual_log_id}",
    response_model=HubspotManualPushLogsDetailResponse,
)
def listing_hubspot_manual_push_log_detail(
    manual_log_id: Optional[int],
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return hubspot_connection_service.hubspot_manual_push_log_detail(
        manual_log_id, db, current_user, listing_plan_code
    )


@router.get(
    "/listing-hubspot-manual-identify-log/{manual_log_id}",
    response_model=HubspotManualIdentifyLogsDetailResponse,
)
def listing_hubspot_manual_identify_log_detail(
    manual_log_id: Optional[int],
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return hubspot_connection_service.hubspot_manual_identify_log_detail(
        manual_log_id, db, current_user, listing_plan_code
    )


@router.get(
    "/listing-hubspot-manual-identify-log",
    response_model=ListingHubspotManualIdentifyLogs,
)
def listing_hubspot_manual_identify_log(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    per_page: Optional[int] = Query(default=10, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
):
    return hubspot_connection_service.listing_hubspot_manual_identify_log(
        db, current_user, per_page, page
    )


@router.post("/manual-push-companies")
def hubspot_manual_push_company(
    request: HubspotManualPushCompanyRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return hubspot_connection_service.hubspot_manual_push_company(
        db=db,
        current_user=current_user,
        request=request,
        listing_plan_code=listing_plan_code,
    )


@router.get("/search-company-hubspot", response_model=SearchCompanyHubspotResponse)
def search_company_hubspot(
    keyword: str = Query(default=""),
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.search_company_hubspot(db, current_user, keyword)


@router.get(
    "/get-synced-company/{corporate_number}", response_model=GetSyncedCompanyResponse
)
def get_synced_company(
    corporate_number: str,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.get_synced_company(
        db, current_user, corporate_number
    )


@router.delete("/delete-synced-company/{corporate_number}", response_model=int)
def delete_synced_company(
    corporate_number: str,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.delete_synced_company(
        db, current_user, corporate_number
    )


@router.post("/create-hubspot-company/{manual_log_id}", response_model=int)
def create_hubspot_company(
    manual_log_id: int,
    request: CreateCompanyHubspotRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.create_hubspot_company(
        db, current_user, request, manual_log_id
    )


@router.post("/match-company/{manual_log_id}")
def match_company_hubspot(
    manual_log_id: int,
    request: MatchCompanyHubspotRequest,
    es_client: Elasticsearch = Depends(get_es),
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.match_company_hubspot(
        db, current_user, request, manual_log_id, es_client
    )


@router.put("/mark-done-error")
def mark_done_error_log(
    request: MarkDoneErrorLogHubspotRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.update_mark_done_error_log(
        db, current_user.team_id, request
    )


@router.post("/manual-sync-companies")
def manual_sync_companies(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.manual_sync_companies(
        db,
        current_user,
    )


@router.post("/manual-sync-persons")
def manual_sync_persons(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.manual_sync_persons(
        db,
        current_user,
    )


@router.post("/manual-sync-affiliated-companies")
def manual_sync_affiliated_companies(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.manual_sync_affiliated_companies(
        db,
        current_user,
    )


@router.get("/statistic/error-log", response_model=HubspotStaticErrorLogResponse)
def get_error_log_count(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.get_error_log_count(db, current_user)


@router.get("/state-auto-batch", response_model=HubspotStateAutoBatchResponse)
def get_state_auto_batch(
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.get_state_auto_batch(db, current_user)


@router.put("/state-auto-batch")
def update_state_auto_batch(
    request: HubspotStateAutoBatchRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    return hubspot_connection_service.update_state_auto_batch(db, current_user, request)
