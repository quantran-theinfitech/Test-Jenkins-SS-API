from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from app.api.v1.schemas.companies import CompanyFormJobResponse
from app.api.v1.schemas.form_templates import FormTemplateBase
from app.api.v1.schemas.placeholders import PlaceholderDetailResponse
from app.models.form_job import FormJobStatusCode, FormJobTypeCode
from app.models.form_job_item import FormJobItemStatusCode


class FormJobMode(Enum):
    RANDOM = "RANDOM"
    EXACT = "EXACT"


class CreateFormJobRequest(BaseModel):
    template_id: int
    placeholder_id: int
    target_collection_id: int
    mode: FormJobMode
    exclude_collection_id: Optional[int] = None
    approach_ng_flag: Optional[bool] = None
    schedule_at: Optional[datetime] = None
    max_resend_code: Optional[str] = None
    form_schedule_id: Optional[int] = None


class CreateFormJobResponse(BaseModel):
    form_job_id: Optional[int] = None


class ListingFormJobsItem(BaseModel):
    id: Optional[int] = None
    team_id: Optional[int] = None
    group_id: Optional[int] = None
    placeholder_id: Optional[int] = None
    placeholder_name: Optional[str] = None
    target_collection_id: Optional[int] = None
    target_collection_name: Optional[str] = None
    exclude_collection_id: Optional[int] = None
    exclude_collection_name: Optional[str] = None
    template_id: Optional[int] = None
    template_title: Optional[str] = None
    approach_ng_flag: Optional[str] = None
    status_code: Optional[FormJobStatusCode] = None
    status_code_item_sum: Optional[FormJobStatusCode] = None
    max_resend_code: Optional[str] = None
    collection_item_count: Optional[int] = None
    success_count: Optional[int] = None
    success_rate: Optional[str] = None
    schedule_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    type_code: Optional[FormJobTypeCode] = None


class ListingFormJobsResponse(BaseModel):
    page: Optional[int] = None
    per_page: Optional[int] = None
    total: Optional[int] = None
    data: List[ListingFormJobsItem]


class FormJobItem(CompanyFormJobResponse):
    company_custom_id: Optional[str] = None
    id: Optional[int] = None
    status_code: Optional[FormJobItemStatusCode] = None
    form_url: Optional[str] = None
    schedule_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ListingFormJobItemsResponse(BaseModel):
    page: Optional[int] = None
    per_page: Optional[int] = None
    total: Optional[int] = None
    contact_form_url_count: Optional[int] = None
    not_send_contact_form_url_count: Optional[int] = None
    job_id: Optional[int] = None
    data: Optional[List[FormJobItem]]


class FormJobDetailResponse(BaseModel):
    id: int
    job_name: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    total: Optional[int] = None
    not_send_contact_form_url_count: Optional[int] = None
    template: FormTemplateBase
    placeholder: PlaceholderDetailResponse
    target_collection_id: int
    exclude_collection_id: Optional[int] = None
    approach_ng_flag: Optional[bool] = None
    schedule_at: Optional[datetime] = None
    max_resend_code: Optional[str] = None
    type_code: Optional[FormJobTypeCode] = None
    form_schedule_id: Optional[int] = None
