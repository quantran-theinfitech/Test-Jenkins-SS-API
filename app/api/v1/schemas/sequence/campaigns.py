# flake8: noqa
import enum
from datetime import datetime
from typing import List, Optional

from fastapi import Query
from pydantic import BaseModel, Field

from app.api.v1.schemas.person_collections import TypeDownloadPerson
from app.models.person import Person
from app.models.sequence.campaign_contacts import StatusEnum
from app.models.sequence.contact import SequencePersonStage
from app.models.sequence.content_items import ContentItemsType
from app.models.sequence.content_template import ContentType
from app.models.sequence.step import (
    FallbackMessageAction,
    Priority,
    ScheduleUnit,
    StepType,
    TimingType,
)


class SequenceCampaignStatusEnum(str, enum.Enum):
    ACTIVE_AND_INACTIVE = "ACTIVE_AND_INACTIVE"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class SequenceCampaignOrderEnum(str, enum.Enum):
    CREATED_AT = "created_at"
    NAME = "name"
    LAST_USED = "last_used"


class SequenceCampaignOrderTypeEnum(str, enum.Enum):
    ASC = "ASC"
    DESC = "DESC"


class CreateCampaignRequest(BaseModel):
    name: str = Field(max_length=255)
    schedule_id: Optional[int] = None


# Same as create campaign request for now
class UpdateCampaignRequest(CreateCampaignRequest):
    is_active: bool


class CampaignEmailStatistic(BaseModel):
    total: Optional[int] = None
    bounced_count: Optional[int] = None
    spam_blocked_count: Optional[int] = None
    scheduled_count: Optional[int] = None
    delivered_count: Optional[int] = None
    reply_count: Optional[int] = None
    open_count: Optional[int] = None
    opt_out_count: Optional[int] = None
    not_sent_count: Optional[int] = None


class CampaignLinkedInStatistic(BaseModel):
    total: int
    scheduled: int
    delivered: int
    bounced: int
    spam_blocked: int
    not_sent: int
    paused: int


class CampaignContactStatistic(BaseModel):
    total: Optional[int] = None
    active_count: Optional[int] = None
    paused_count: Optional[int] = None
    not_sent_count: Optional[int] = None
    bounced_count: Optional[int] = None
    finished_count: Optional[int] = None


class StepStatistic(BaseModel):
    email_statistic: Optional[CampaignEmailStatistic] = None
    contact_statistic: Optional[CampaignContactStatistic] = None
    linkedin_statistic: Optional[CampaignLinkedInStatistic] = None


class CampaignStatistic(BaseModel):
    email_statistic: Optional[CampaignEmailStatistic] = None
    contact_statistic: Optional[CampaignContactStatistic] = None
    linkedin_statistic: Optional[CampaignLinkedInStatistic] = None


class CampaignContactStatisticBase(BaseModel):
    contact_statistic: Optional[CampaignContactStatistic] = None


class ContentTemplateBase(BaseModel):
    id: int
    title: Optional[str]
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    content: Optional[str]
    content_type: Optional[ContentType] = None


class ContentTemplateItemBase(BaseModel):
    id: int
    step_content_template_id: Optional[int]
    type: Optional[ContentItemsType]
    mime_type: Optional[str]
    content: Optional[str]
    file_path: Optional[str]
    file_name: Optional[str]
    order: Optional[int]


class StepBase(BaseModel):
    id: int
    sequence_campaign_id: int
    content_template_id: Optional[int] = None
    step_type: StepType
    is_active_not_allowed: Optional[bool] = None
    description: str
    timing_type: TimingType
    schedule_unit: Optional[ScheduleUnit] = None
    schedule_value: Optional[int] = None
    priority: Optional[Priority] = None
    memo: Optional[str] = None
    is_email_limit_enabled: bool
    email_limit_count: Optional[int] = None
    is_skip_enabled: bool
    skip_after_days: Optional[int] = None
    is_active: bool
    order: int
    statistic: Optional[StepStatistic] = None
    content_template: Optional[ContentTemplateBase] = None
    template_items: Optional[List[ContentTemplateItemBase]] = None
    total_days: Optional[int] = None
    fallback_message_action: Optional[FallbackMessageAction] = None


class StepList(BaseModel):
    data: List[StepBase]


class SequenceBase(BaseModel):
    id: int
    created_by: int
    created_at: datetime
    name: str
    is_active: bool
    owner_id: int
    owner_name: Optional[str] = None
    owner_avatar: Optional[str] = None
    steps: List[StepBase] = []
    statistic: Optional[CampaignStatistic] = None
    have_contact: bool = False
    is_first_active: bool = False


class SequenceCampaignListBase(BaseModel):
    id: int
    created_by: int
    created_at: datetime
    name: str
    is_active: bool
    owner_id: int
    owner_name: Optional[str] = None
    owner_avatar: Optional[str] = None
    steps: List[StepBase] = []
    statistic: Optional[CampaignContactStatisticBase] = None
    have_contact: bool = False
    is_first_active: bool = False


class ListingCampaignRequest(BaseModel):
    name: Optional[str] = Query(default=None)
    per_page: Optional[int] = Query(default=10, le=50, ge=1)
    page: Optional[int] = Query(default=1, ge=1)
    is_active: Optional[bool] = Query(default=None)
    order_by: Optional[SequenceCampaignOrderEnum] = Query(
        default=SequenceCampaignOrderEnum.CREATED_AT,
        description="Field to order by. Valid options: `name`, `created_at`, `updated_at`",
    )
    order_type: Optional[SequenceCampaignOrderTypeEnum] = Query(
        default=SequenceCampaignOrderTypeEnum.DESC
    )
    status: Optional[SequenceCampaignStatusEnum] = Query(
        default=SequenceCampaignStatusEnum.ACTIVE_AND_INACTIVE
    )


class ListingImportContactsRequest(BaseModel):
    name: Optional[str] = Query(default=None)
    per_page: Optional[int] = Query(default=10, le=50, ge=1)
    page: Optional[int] = Query(default=1, ge=1)


class SequenCampaignDetailResponse(SequenceBase):
    deleted_at: Optional[datetime] = None


class ListingSequenceResponse(BaseModel):
    page: int
    per_page: int
    total: int
    data: List[SequenCampaignDetailResponse]


class SequenceImportContactsBase(BaseModel):
    id: int
    name: str


class ListingSequenceImportContactsResponse(BaseModel):
    page: int
    per_page: int
    total: int
    data: List[SequenceImportContactsBase]


class SequenceDetailResponse(SequenceBase):
    schedule_id: int


class ContactBase(BaseModel):
    id: int
    name: str
    email: str
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    hubspot_id: Optional[str] = None
    phone: Optional[str] = None
    status: str
    current_step: int
    company_id: int


class ListingContactResponse(BaseModel):
    page: int
    per_page: int
    total: int
    data: List[ContactBase]


class SequenceStatus(BaseModel):
    action: str
    action_date: datetime


class ContactDetailResponse(ContactBase):
    sequence_name: str
    added_on: datetime
    added_by: int
    status_history: List[SequenceStatus]


class AddStepRequest(BaseModel):
    step_type: StepType
    description: str
    timing_type: TimingType
    schedule_unit: Optional[ScheduleUnit] = None
    schedule_value: Optional[int] = None
    priority: Optional[Priority] = None
    memo: Optional[str] = None
    is_email_limit_enabled: Optional[bool] = False
    email_limit_count: Optional[int] = None
    is_skip_enabled: Optional[bool] = False
    skip_after_days: Optional[int] = None
    fallback_message_action: Optional[FallbackMessageAction] = None


class DeleteCampaignRequest(BaseModel):
    campaign_ids: List[int]


class UpdateStepRequest(AddStepRequest):
    is_active: bool


class UpdateCampaignResponse(BaseModel):
    is_credit_warning: bool
    is_mailbox_warning: bool
    is_linkedin_warning: bool


class AddContactRequest(BaseModel):
    is_mailbox_rotation_enabled: bool
    is_contact_validation_skipped: bool
    add_schedule_to_sequence: str
    custom_schedule_time: datetime


class PersonStages(BaseModel):
    total: int
    new: int
    open: int
    in_progress: int
    open_deal: int
    unqualified: int
    attempted_to_contacts: int
    connected: int
    bad_timing: int
    no_stage: int
    all_in_progress_stages: int
    all_succeeded_stages: int
    all_failed_stages: int


class UpdateCampaignPersonsRequest(BaseModel):
    status: StatusEnum
    sequence_person_ids: List[int]
    reason: Optional[str]
    time_resumed: Optional[datetime]

    class Config:
        use_enum_values = True


class ListingSequenceOwnerResponse(BaseModel):
    id: int
    name: Optional[str]
    is_current_user: bool = False


class ReorderCampaignStepsRequest(BaseModel):
    step_id: int
    previous_step_id: Optional[int] = None


class ContactPreviewInfo(BaseModel):
    id: Optional[int]
    uuid: Optional[str]
    sequence_campaign_id: Optional[int]
    target_type: Optional[str]
    name: Optional[str]
    role_name: Optional[List[Optional[str]]]
    email: Optional[str]
    linkedin_url: Optional[str]
    twitter_url: Optional[str]
    github_url: Optional[str]
    note_url: Optional[str]
    fb_url: Optional[str]
    wantedly_url: Optional[str]
    skills: Optional[str]
    corporate_number: Optional[List[Optional[str]]]
    status: Optional[str]
    current_step: Optional[int]
    stage: Optional[SequencePersonStage] = SequencePersonStage.COLD
    company_name: Optional[List[Optional[str]]]
    wantedly_id: Optional[str]
    address: Optional[str]
    linkedin_internal_id: Optional[str]
    intro: Optional[str]
    bio: Optional[str]
    role_code: Optional[str]
    role_group_codes: Optional[List[str]]


class ContactStatisticsBase(BaseModel):
    total: Optional[int] = 0
    contacts: Optional[List[ContactPreviewInfo]] = None


class GetPreviewContactResponse(BaseModel):
    new_contacts: ContactStatisticsBase
    restored_contacts: ContactStatisticsBase
    incomplete_contacts: ContactStatisticsBase
    duplicate_contacts: ContactStatisticsBase
    total: int


class GetContactUuidsRequest(BaseModel):
    type_download_person: Optional[TypeDownloadPerson] = None
    contact_uuids: Optional[List[str]] = None
    collection_list_id: Optional[int] = None


class AddSequenceContactRequest(BaseModel):
    sequence_campaign_id: int
    type_download_person: TypeDownloadPerson
    contact_uuids: List[str]
    is_include_incompleted_contacts: Optional[bool]


class AddSequenceContactResponse(BaseModel):
    success: bool
