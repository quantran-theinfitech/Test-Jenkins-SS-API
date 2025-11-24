from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class StatusLog(str, Enum):
    PENDING = 0
    SUCCESS = 1
    FAILED = 2


class TypePush(str, Enum):
    DOWNLOADED = "DOWNLOADED"
    CREDIT = "CREDIT"


class TypeSync(str, Enum):
    PUSH_TO_HUBSPOT = "PUSH"
    PULL_FROM_HUBSPOT = "PULL"
    IDENTIFY_PERSON = "PERSON"


class ErrorType(str, Enum):
    MULTI = "MULTIPLE"
    NOTFOUND = "NOTFOUND"
    NOT_ENOUGH_CREDIT = "NOT_ENOUGH_CREDIT"


class HubspotConnectionResponse(BaseModel):
    connection_id: Optional[int]
    email: Optional[str] = None
    hubspot_team_id: Optional[str] = None
    status: bool


class HubspotConnectionDetailResponse(BaseModel):
    email: Optional[str] = None
    hubspot_team_id: Optional[int] = None


class HubspotMapping(BaseModel):
    sale_smart_field: Optional[str]
    hubspot_field: Optional[str]
    is_over_write: Optional[bool]
    is_auto_fill: Optional[bool]


class HubspotMappingSettingResponse(BaseModel):
    connection_id: Optional[int] = None
    mapping_field: Optional[List[HubspotMapping]]


class HubspotCompanySchema(BaseModel):
    name: Optional[str] = None
    label: Optional[str] = None
    type_field: Optional[str] = None
    group: Optional[str] = None


class HubspotCompanySchemaResponse(BaseModel):
    connection_id: Optional[int]
    data: List[HubspotCompanySchema]


class SaleSmartSchema(BaseModel):
    name: Optional[str] = None
    label: Optional[str] = None
    type_field: Optional[str] = None


class SaleSmartCompanySchemaResponse(BaseModel):
    connection_id: Optional[int]
    data: List[SaleSmartSchema]


class UpdateMappingFieldRequest(BaseModel):
    data: Optional[List[HubspotMapping]] = None


class CreateCompanyHubspotRequest(BaseModel):
    type_create: Optional[TypeSync] = None
    hubspot_person_id: Optional[str] = None
    ss_company_corporate_number: Optional[str] = None
    downloaded_flag: Optional[str] = None


class MatchCompanyHubspotRequest(BaseModel):
    type_match: Optional[TypeSync] = None
    ss_corporate_number: Optional[str] = None
    hubspot_company_id: Optional[str] = None
    downloaded_flag: Optional[bool] = None


class MarkDoneErrorLogHubspotRequest(BaseModel):
    type_match: Optional[TypeSync] = None
    hubspot_company_id: Optional[str] = None
    hubspot_person_id: Optional[str] = None


class HubspotSyncLogs(BaseModel):
    id: int
    status: Optional[int] = None
    type_log: Optional[str] = None
    created_at: Optional[datetime] = None
    total_companies: Optional[int] = None
    error_message: Optional[str] = None
    match_error_count: Optional[int] = None
    match_success_count: Optional[int] = None
    sync_count: Optional[int] = None


class HubspotManualPullLogs(BaseModel):
    id: int
    hubspot_team_id: Optional[str] = None
    hubspot_company_id: Optional[int] = None
    hub_company_name: Optional[str] = None
    error_type: Optional[str] = None
    created_at: Optional[datetime] = None


class HubspotManualPullLogsDetail(BaseModel):
    ss_corporate_number: Optional[str] = None
    ss_company_name: Optional[str] = None
    domain: Optional[str] = None
    is_downloaded: Optional[bool] = None
    favicon_url: Optional[str] = None
    president_name: Optional[str] = None


class HubspotManualPushLogsDetail(BaseModel):
    hubspot_company_id: Optional[int] = None
    hubspot_company_name: Optional[str] = None
    domain: Optional[str] = None


class HubspotManualIdentifyLogsDetail(BaseModel):
    ss_corporate_number: Optional[str] = None
    ss_company_name: Optional[str] = None
    domain: Optional[str] = None
    is_downloaded: Optional[bool] = None
    favicon_url: Optional[str] = None
    president_name: Optional[str] = None


class HubspotManualPushLogs(BaseModel):
    id: int
    ss_corporate_number: Optional[str] = None
    ss_company_name: Optional[str] = None
    error_type: Optional[str] = None
    created_at: Optional[datetime] = None
    is_downloaded: Optional[bool] = None


class HubspotManualIdentifyLogs(BaseModel):
    id: int
    hubspot_team_id: Optional[str] = None
    hubspot_person_id: Optional[int] = None
    hub_person_name: Optional[str] = None
    error_type: Optional[str] = None
    created_at: Optional[datetime] = None


class ListingHubspotSyncLogs(BaseModel):
    per_page: Optional[int] = None
    page: Optional[int] = None
    total: Optional[int] = None
    data: Optional[List[HubspotSyncLogs]] = None


class ListingHubspotManualPullLogs(BaseModel):
    per_page: Optional[int] = None
    page: Optional[int] = None
    total: Optional[int] = None
    data: Optional[List[HubspotManualPullLogs]] = None


class HubspotManualPullLogsDetailResponse(BaseModel):
    total: Optional[int] = None
    hubspot_company_id: Optional[int] = None
    hubspot_company_name: Optional[str]
    created_at: Optional[datetime] = None
    error_type: Optional[str] = None
    data: Optional[List[HubspotManualPullLogsDetail]] = None


class HubspotManualPushLogsDetailResponse(BaseModel):
    total: Optional[int] = None
    ss_corporate_number: Optional[str] = None
    ss_company_name: Optional[str]
    is_downloaded: Optional[bool]
    created_at: Optional[datetime] = None
    error_type: Optional[str] = None
    data: Optional[List[HubspotManualPushLogsDetail]] = None


class HubspotManualIdentifyLogsDetailResponse(BaseModel):
    total: Optional[int] = None
    hubspot_person_id: Optional[int] = None
    hub_person_name: Optional[str] = None
    hubspot_company_id: Optional[str] = None
    hubspot_company_name: Optional[str] = None
    error_type: Optional[str] = None
    data: Optional[List[HubspotManualIdentifyLogsDetail]] = None
    created_at: Optional[datetime] = None


class ListingHubspotManualPushLogs(BaseModel):
    per_page: Optional[int] = None
    page: Optional[int] = None
    total: Optional[int] = None
    data: Optional[List[HubspotManualPushLogs]] = None


class ListingHubspotManualIdentifyLogs(BaseModel):
    per_page: Optional[int] = None
    page: Optional[int] = None
    total: Optional[int] = None
    data: Optional[List[HubspotManualIdentifyLogs]] = None


class HubspotManualPushCompanyRequest(BaseModel):
    type_push: Optional[TypePush] = None
    corporate_numbers: Optional[List[str]] = None


class SearchCompanyHubspot(BaseModel):
    hubspot_company_id: Optional[str] = None
    company_name: Optional[str] = None
    domain: Optional[str] = None


class SearchCompanyHubspotResponse(BaseModel):
    total: Optional[int] = None
    data: Optional[List[SearchCompanyHubspot]]


class GetSyncedCompanyResponse(BaseModel):
    is_synced: Optional[bool]
    ss_company_name: Optional[str] = None
    hubspot_team_id: Optional[str] = None
    hubspot_company_id: Optional[str] = None
    hubspot_company_name: Optional[str] = None


class FieldHubspotRequest(BaseModel):
    label: Optional[str] = None
    name: Optional[str] = None
    type_field: Optional[str] = None
    group: Optional[str] = None


class HubspotCreateFieldRequest(BaseModel):
    custom_field: List[FieldHubspotRequest] = []


class HubspotStateAutoBatchResponse(BaseModel):
    auto_pull_companies: Optional[bool] = None
    auto_pull_persons: Optional[bool] = None
    auto_sync_companies: Optional[bool] = None
    last_time_pull_companies: Optional[datetime] = None
    last_time_pull_persons: Optional[datetime] = None
    last_time_sync_companies: Optional[datetime] = None


class HubspotStateAutoBatchRequest(BaseModel):
    auto_pull_companies: Optional[bool] = None
    auto_pull_persons: Optional[bool] = None
    auto_sync_companies: Optional[bool] = None


class HubspotStaticErrorLogResponse(BaseModel):
    total: Optional[int] = None
    total_push_history: Optional[int] = None
    total_pull_history: Optional[int] = None
