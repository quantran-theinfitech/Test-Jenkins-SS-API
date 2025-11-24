import enum
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.api.v1.schemas.sequence.linkedin_account import LinkedInAccountBase
from app.api.v1.schemas.sequence.mail_histories import ScheduleType
from app.models.sequence.linkedin_activities import (
    LinkedinHistoryProcessStatus,
    LinkedinHistoryStatus,
)
from app.models.sequence.mail_history import AccountOption, MailHistoryStatus


class SortField(str, enum.Enum):
    SENT_DATE = "sent_date"


class SortOrder(str, enum.Enum):
    ASC = "ASC"
    DESC = "DESC"


class LinkedInActivityType(str, enum.Enum):
    LINKEDIN_AUTO_MESSAGE = "LINKEDIN_AUTO_MESSAGE"
    LINKEDIN_CONNECTION_REQUEST = "LINKEDIN_CONNECTION_REQUEST"
    LINKEDIN_VIEW_PROFILE = "LINKEDIN_VIEW_PROFILE"


class LinkedInActivityStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    DELIVERED = "DELIVERED"
    NOT_SENT = "NOT_SENT"
    SPAM_BLOCKED = "SPAM_BLOCKED"
    BOUNCED = "BOUNCED"
    PAUSED = "PAUSED"
    FAILED = "FAILED"


class LinkedInActivityBase(BaseModel):
    mail_history_id: Optional[int] = None
    sequence_campaign_id: Optional[int] = None
    sequence_step_id: Optional[int] = None
    sequence_contact_id: Optional[int] = None
    sequence_linkedin_account_id: Optional[int] = None
    thread_id: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    status: Optional[MailHistoryStatus] = None
    process_status: Optional[LinkedinHistoryProcessStatus] = None
    next_sequence_step_id: Optional[int] = None
    sent_at: Optional[datetime] = None
    to_address: Optional[str] = None
    replied_at: Optional[datetime] = None
    is_rescheduled: Optional[bool] = None
    tracking_token: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    linkedin: Optional[LinkedInAccountBase] = None
    sequence_campaign_name: Optional[str] = None
    sequence_step_order: Optional[int] = None
    step_type: Optional[str] = None
    sequence_person_name: Optional[str] = None
    sequence_contact_email: Optional[str] = None
    sequence_linkedin_account_name: Optional[str] = None
    sender_name: Optional[str] = None
    sender_avatar: Optional[str] = None
    sent_by: Optional[int] = None
    account_option: Optional[AccountOption] = AccountOption.DEFAULT
    fail_reason: Optional[str] = None


class ListingLinkedInActivityResponse(BaseModel):
    page: int
    per_page: int
    total: int
    data: List[LinkedInActivityBase]


class LinkedInActivityStatistics(BaseModel):
    total: int
    scheduled: int
    delivered: int
    bounced: int
    spam_blocked: int
    not_sent: int
    paused: int
    failed: int


class LinkedInActivityStepStatistics(BaseModel):
    scheduled: int
    delivered: int
    bounced: int
    spam_blocked: int
    not_sent: int
    paused: int


class LinkedInActivityActionRequest(BaseModel):
    campaign_id: int
    contact_id: int
    step_id: int


class RescheduleLinkedInActivityRequest(BaseModel):
    linkedin_activities: List[LinkedInActivityActionRequest]
    schedule_type: ScheduleType
    custom_datetime: Optional[datetime] = None


class RescheduleLinkedInActivityResponse(BaseModel):
    success: bool


class DeleteLinkedInActivityRequest(BaseModel):
    linkedin_activities: List[LinkedInActivityActionRequest]


class DeleteLinkedInActivityResponse(BaseModel):
    success: bool


class RetryLinkedInActivityRequest(BaseModel):
    linkedin_activities: List[LinkedInActivityActionRequest]


class RetryLinkedInActivityResponse(BaseModel):
    success: bool


class SkipLinkedInActivityRequest(BaseModel):
    linkedin_activities: List[LinkedInActivityActionRequest]


class SkipLinkedInActivityResponse(BaseModel):
    success: bool


class ChangeLinkedInAccountHistoryRequest(BaseModel):
    linkedin_activities: List[LinkedInActivityActionRequest]
    account_option: AccountOption = AccountOption.DEFAULT
    linkedin_account_id: int


class ChangeLinkedInAccountHistoryResponse(BaseModel):
    success: bool


class ListingLinkedInActivityRequest(BaseModel):
    page: int
    per_page: int
    sort: SortField
    order: Optional[SortOrder] = None
    keyword: Optional[str] = None
    types: List[LinkedInActivityType]
    statuses: Optional[List[LinkedInActivityStatus]] = None
    step_ids: Optional[List[int]] = None
    linkedin_user_id: Optional[int] = None
    linkedin_senders: Optional[List[str]] = None
