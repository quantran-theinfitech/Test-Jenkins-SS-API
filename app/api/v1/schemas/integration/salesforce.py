from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.api.v1.schemas.hubspot_connections import TypePush, TypeSync


class SalesforceIntegrationResponse(BaseModel):
    connection_id: Optional[int]
    email: Optional[str] = None
    salesforce_team_id: Optional[str] = None
    status: bool


class SalesforceIntegrationDetailResponse(BaseModel):
    email: Optional[str] = None
    salesforce_team_id: Optional[str] = None


class SalesforceFieldMapping(BaseModel):
    sale_smart_field: Optional[str]
    salesforce_field: Optional[str]
    is_over_write: Optional[bool]
    is_auto_fill: Optional[bool]
    field_class: Optional[str]


class SalesforceListingFieldMappingResponse(BaseModel):
    connection_id: Optional[int] = None
    mapping_field: Optional[List[SalesforceFieldMapping]] = []


class SalesforceCompanySchema(BaseModel):
    name: Optional[str] = None
    label: Optional[str] = None
    type: Optional[str] = None


class SalesforceListingCompnaySchemaResponse(BaseModel):
    connection_id: Optional[int]
    data: Optional[List[SalesforceCompanySchema]] = []


class SalesforceUpdateMappingFieldRequest(BaseModel):
    data: Optional[List[SalesforceFieldMapping]] = []


class SalesforceSyncLogItem(BaseModel):
    id: int
    status: Optional[int] = None
    type_log: Optional[str] = None
    created_at: Optional[datetime] = None
    total_companies: Optional[int] = None
    error_message: Optional[str] = None
    match_error_count: Optional[int] = None
    match_success_count: Optional[int] = None
    sync_count: Optional[int] = None


class ListingSalesforceSyncLogsResponse(BaseModel):
    per_page: Optional[int] = None
    page: Optional[int] = None
    total: Optional[int] = None
    data: Optional[List[SalesforceSyncLogItem]] = []


class SalesforceManualPushCompanyRequest(BaseModel):
    type_push: Optional[TypePush] = None
    corporate_numbers: Optional[List[str]] = None


class SalesforcePushErrorLogItem(BaseModel):
    id: int
    is_downloaded: Optional[bool] = None
    created_at: Optional[datetime] = None
    error_type: Optional[str] = None
    ss_corporate_number: Optional[str] = None
    ss_company_name: Optional[str] = None


class ListingSalesforcePushErrorLogsResponse(BaseModel):
    per_page: Optional[int] = None
    page: Optional[int] = None
    total: Optional[int] = None
    data: Optional[List[SalesforcePushErrorLogItem]] = []


class SalesforcePullErrorLogItem(BaseModel):
    id: int
    salesforce_team_id: Optional[str] = None
    salesforce_company_id: Optional[str] = None
    salesforce_company_name: Optional[str] = None
    error_type: Optional[str] = None
    created_at: Optional[datetime] = None
    url: Optional[str] = None


class ListingSalesforcePullErrorLogsResponse(BaseModel):
    per_page: Optional[int] = None
    page: Optional[int] = None
    total: Optional[int] = None
    data: Optional[List[SalesforcePullErrorLogItem]] = []


class SalesforcePullPersonErrorLogItem(BaseModel):
    id: int
    salesforce_team_id: Optional[str] = None
    salesforce_person_id: Optional[str] = None
    salesforce_person_name: Optional[str] = None
    error_type: Optional[str] = None
    created_at: Optional[datetime] = None
    url: Optional[str] = None


class ListingSalesforcePullPersonErrorLogsResponse(BaseModel):
    per_page: Optional[int] = None
    page: Optional[int] = None
    total: Optional[int] = None
    data: Optional[List[SalesforcePullPersonErrorLogItem]] = []


class SalesforcePushErrorLogCompany(BaseModel):
    salesforce_company_id: Optional[str] = None
    salesforce_company_name: Optional[str] = None
    domain: Optional[str] = None


class SalesforcePushErrorLogDetailResponse(BaseModel):
    total: Optional[int] = None
    ss_corporate_number: Optional[str] = None
    ss_company_name: Optional[str]
    is_downloaded: Optional[bool]
    created_at: Optional[datetime] = None
    error_type: Optional[str] = None
    data: Optional[List[SalesforcePushErrorLogCompany]] = None


class ListingSalesforceCompaniesResponse(BaseModel):
    total: Optional[int] = None
    data: Optional[List[SalesforcePushErrorLogCompany]] = None


class SalesforceCreateCompanyRequest(BaseModel):
    type_create: Optional[TypeSync] = None
    ss_company_corporate_number: Optional[str] = None
    downloaded_flag: Optional[str] = None


class SalesforceMatchCompanyRequest(BaseModel):
    type_match: Optional[TypeSync] = None
    ss_corporate_number: Optional[str] = None
    salesforce_company_id: Optional[str] = None
    downloaded_flag: Optional[bool] = None


class SalesforcePullErrorLogCompany(BaseModel):
    ss_corporate_number: Optional[str] = None
    ss_company_name: Optional[str] = None
    domain: Optional[str] = None
    is_downloaded: Optional[bool] = None
    favicon_url: Optional[str] = None
    president_name: Optional[str] = None


class SalesforcePullErrorLogDetailResponse(BaseModel):
    total: Optional[int] = None
    created_at: Optional[datetime] = None
    error_type: Optional[str] = None
    salesforce_company_id: Optional[str] = None
    salesforce_company_name: Optional[str] = None
    url: Optional[str] = None
    data: Optional[List[SalesforcePullErrorLogCompany]] = None


class SalesforcePullPersonErrorLog(BaseModel):
    ss_corporate_number: Optional[str] = None
    ss_company_name: Optional[str] = None
    domain: Optional[str] = None
    is_downloaded: Optional[bool] = None
    favicon_url: Optional[str] = None
    president_name: Optional[str] = None


class SalesforcePullPersonErrorLogDetailResponse(BaseModel):
    total: Optional[int] = None
    created_at: Optional[datetime] = None
    error_type: Optional[str] = None
    salesforce_person_id: Optional[str] = None
    salesforce_person_name: Optional[str] = None
    url: Optional[str] = None
    data: Optional[List[SalesforcePullPersonErrorLog]] = None


class SalesforceMarkDoneErrorLogRequest(BaseModel):
    type_match: Optional[TypeSync] = None
    salesforce_company_id: Optional[str] = None
    salesforce_person_id: Optional[str] = None


class SalesforceFieldRequest(BaseModel):
    label: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    group: Optional[str] = None


class SalesforceCreateCustomFieldRequest(BaseModel):
    custom_field: List[SalesforceFieldRequest] = []


class SalesforceSyncedCompanyResponse(BaseModel):
    is_synced: Optional[bool]
    ss_company_name: Optional[str] = None
    salesforce_team_id: Optional[str] = None
    salesforce_company_id: Optional[str] = None
    salesforce_company_name: Optional[str] = None
    url: Optional[str] = None


class SalesforceStateAutoBatchResponse(BaseModel):
    auto_pull_companies: Optional[bool] = None
    auto_pull_persons: Optional[bool] = None
    auto_sync_companies: Optional[bool] = None
    last_time_pull_companies: Optional[datetime] = None
    last_time_pull_persons: Optional[datetime] = None
    last_time_sync_companies: Optional[datetime] = None


class SalesforceStateAutoBatchRequest(BaseModel):
    auto_pull_companies: Optional[bool] = None
    auto_pull_persons: Optional[bool] = None
    auto_sync_companies: Optional[bool] = None


class SalesforceStaticErrorLogResponse(BaseModel):
    total: Optional[int] = None
    total_push_history: Optional[int] = None
    total_pull_history: Optional[int] = None
