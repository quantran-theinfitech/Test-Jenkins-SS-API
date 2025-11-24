import enum
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.sequence.mail_history import MailHistoryStatus

from .mailboxes import MailboxBase


class MailHistoryType(str, enum.Enum):
    FUTURE = "FUTURE"
    HISTORY = "HISTORY"
    FIRST = "FIRST"


class MailHistoryBase(BaseModel):
    sequence_contact_id: Optional[int]
    sequence_person_name: Optional[str]
    sequence_campaign_id: Optional[int]
    sequence_campaign_name: Optional[str]
    sequence_step_id: Optional[int]
    sequence_step_order: Optional[int]
    sequence_mailbox_id: Optional[int]
    sequence_mailbox_alias_id: Optional[int]
    email_from: Optional[str]
    title: Optional[str]
    content: Optional[str]
    to_address: Optional[str]
    is_reply_to_previous_thread: Optional[bool]
    status: Optional[MailHistoryStatus]
    sent_at: Optional[datetime]
    sent_by: Optional[int]
    sender_name: Optional[str]
    sender_avatar: Optional[str]
    mail_history_type: Optional[MailHistoryType]
    mailbox: Optional[MailboxBase]
    email_signature: Optional[str] = None
    opt_out_message: Optional[str] = None
    is_include_opt_out_and_signature: Optional[bool] = False
    fail_reason: Optional[str] = None


class MailHistoryStatistics(BaseModel):
    total: int
    not_sent_count: int
    draft_count: int
    delivered_count: int
    opened_count: int
    replied_count: int
    scheduled_count: int
    unsubscribed_count: int
    bounced_count: Optional[int] = None
    spam_blocked_count: Optional[int] = None
    failed_count: Optional[int] = None


class ListingMailHistoryRequest(BaseModel):
    page: int
    per_page: int
    status: Optional[MailHistoryStatus]
    mailbox_ids: Optional[List[int]]
    step_ids: Optional[List[int]]
    contact_ids: Optional[List[int]]
    keyword: Optional[str]
    mail_senders: Optional[List[str]]


class ListingMailHistoryResponse(BaseModel):
    page: int
    per_page: int
    total: Optional[int]
    data: List[MailHistoryBase]


class ScheduleType(str, enum.Enum):
    CUSTOM = "CUSTOM"
    IMMEDIATELY = "IMMEDIATELY"
    ONE_HOUR = "ONE_HOUR"
    TWO_HOUR = "TWO_HOUR"
    A_DAY = "A_DAY"
    A_WEEK = "A_WEEK"
    A_MONTH = "A_MONTH"
    NEXT_BUSINESS_DAY_MORNING = "NEXT_BUSINESS_DAY_MORNING"
    NEXT_BUSINESS_DAY_AFTERNOON = "NEXT_BUSINESS_DAY_AFTERNOON"


class MailHistoryActionRequest(BaseModel):
    campaign_id: int
    person_id: int
    step_id: int


class SkipMailHistoryStatusRequest(BaseModel):
    mail_histories: List[MailHistoryActionRequest]


class RescheduleMailHistoryStatusRequest(BaseModel):
    mail_histories: List[MailHistoryActionRequest]
    schedule_type: ScheduleType
    custom_datetime: Optional[datetime]


class ChangeMailboxMailHistoryRequest(BaseModel):
    mail_histories: List[MailHistoryActionRequest]
    mailbox_id: int
    mailbox_alias_id: Optional[int]
    is_change_subsequent_steps: bool


class RetryMailHistoryRequest(BaseModel):
    mail_histories: List[MailHistoryActionRequest]


class DeleteMailHistoryRequest(BaseModel):
    mail_histories: List[MailHistoryActionRequest]
