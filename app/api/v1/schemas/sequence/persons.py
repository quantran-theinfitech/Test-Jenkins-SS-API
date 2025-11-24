from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from app.api.v1.schemas.sequence.campaigns import SequenceBase, StatusEnum
from app.api.v1.schemas.sequence.tasks import TaskBase
from app.models.sequence.campaign_import import UploadProcessStatus
from app.models.sequence.contact import SequencePersonStage


class SequenceStatus(BaseModel):
    action: str
    action_date: datetime


class SequencePersonStatisticsBase(BaseModel):
    id: Optional[int] = None
    sequence_person_id: Optional[int] = None
    last_activity: Optional[datetime] = None
    email_last_opened_at: Optional[datetime] = None
    times_opened: Optional[int] = None
    created_at: Optional[datetime] = None


class SequencePersonsBase(BaseModel):
    id: int
    uuid: str
    name: str
    email: Optional[str] = None
    address: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    hubspot_id: Optional[str] = None
    github_url: Optional[str] = None
    note_url: Optional[str] = None
    fb_url: Optional[str] = None
    wantedly_url: Optional[str] = None
    phone: Optional[str] = None
    intro: Optional[str] = None
    bio: Optional[str] = None
    role_code: Optional[str] = None
    role_name: Optional[List[str]] = None
    skills: Optional[str] = None
    corporate_number: Optional[List[str]] = None
    company_name: Optional[List[str]] = None
    current_step: Optional[int] = None
    stage: Optional[SequencePersonStage] = None
    created_at: Optional[datetime] = None


class SequencePersonStatus(BaseModel):
    campaign: Optional[SequenceBase] = None
    person: Optional[SequencePersonsBase] = None
    person_statistics: Optional[SequencePersonStatisticsBase] = None
    status: Optional[StatusEnum] = None


class SequencePersonStageStatistic(BaseModel):
    total: Optional[int] = None
    cold_count: Optional[int] = None
    approaching_count: Optional[int] = None
    unresponsive_count: Optional[int] = None
    bad_data_count: Optional[int] = None
    do_not_contact_count: Optional[int] = None
    replied_count: Optional[int] = None


class SequenceContactUploadResponse(BaseModel):
    success: bool
    err_message: Optional[str] = None
    request_skipping_blank_contact: bool
    blank_contact_count: int


class ListingSequencePersonsResponse(BaseModel):
    page: int
    per_page: int
    total: int
    data: List[SequencePersonStatus]
    import_process_status: UploadProcessStatus


class ListingSequencePersonFromCsv(BaseModel):
    data: List[SequencePersonStatus]


class SequencePersonDetailResponse(SequencePersonsBase):
    sequence_name: str
    added_on: datetime
    added_by: int
    status_history: List[SequenceStatus]


class SequenceCampaignWithPersonStatus(SequenceBase):
    status: Optional[StatusEnum] = None


class SequencePersonDetail(SequencePersonsBase):
    campaigns: List[SequenceCampaignWithPersonStatus]
    tasks: List[TaskBase]


class SortOrder(str, Enum):
    ASC = "ASC"
    DESC = "DESC"


class SortField(str, Enum):
    CREATED_AT = "created_at"
    LAST_ACTIVITY = "last_activity"
    EMAIL_LAST_OPENED_AT = "email_last_opened_at"
    EMAIL_LAST_CLICKED_AT = "email_last_clicked_at"
    TIMES_OPENED = "times_opened"
    TIMES_CLICKED = "times_clicked"
    NAME = "name"
    COMPANY_NAME = "company_name"


class SortRequest(BaseModel):
    order: Optional[SortOrder] = SortOrder.DESC
    field: Optional[SortField] = SortField.CREATED_AT


class UpdateSequencePersonStageRequest(BaseModel):
    stage: Optional[SequencePersonStage] = None
    sequence_person_ids: Optional[List[int]] = None


class UpdateSequencePersonRequest(BaseModel):
    stage: Optional[SequencePersonStage] = None
    name: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None


class SequencePersonStageResponse(BaseModel):
    sequence_person_ids: Optional[List[int]] = None


class ChangeSequencePersonMailbox(BaseModel):
    sequence_person_ids: Optional[List[int]] = None
    mailbox_id: int
    mailbox_alias_id: Optional[int]


class CampaignImportBase(BaseModel):
    sequence_campaign_import_id: int
    sequence_campaign_import_name: str


class CampaignImportList(BaseModel):
    data: List[CampaignImportBase]
