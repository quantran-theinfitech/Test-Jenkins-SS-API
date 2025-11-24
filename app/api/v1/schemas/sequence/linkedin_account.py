import enum
from datetime import datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.sequence.linkedin_account import (
    FirstStepConfigEnum,
    LinkedInAccountStatus,
)


class ConnectType(str, enum.Enum):
    create = "create"
    reconnect = "reconnect"


class HostedAuthUrlRequest(BaseModel):
    type: ConnectType
    account_id: Optional[str] = None
    expiresOn: Optional[datetime] = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(minutes=10)
    )


class HostedAuthUrlResponse(BaseModel):
    object: str
    url: str


class HostedAuthCallback(BaseModel):
    account_id: str
    name: str
    status: LinkedInAccountStatus


class ListingAccountItem(BaseModel):
    account_id: str
    account_name: str
    account_type: str
    status: LinkedInAccountStatus
    is_default: Optional[bool]

    class Config:
        orm_mode = True


class ListingAccountResponse(BaseModel):
    page: Optional[int]
    per_page: Optional[int]
    total: int
    data: List[ListingAccountItem]


class ListingAllAccountItem(BaseModel):
    id: int
    name: str
    is_default: bool


class ListingAllAccountResponse(BaseModel):
    data: List[ListingAllAccountItem]


class ConfigAccountRequest(BaseModel):
    messages_sent_per_day: Optional[int] = None
    messages_sent_per_week: Optional[int] = None
    connections_sent_per_day: Optional[int] = None
    connections_sent_per_week: Optional[int] = None
    profile_views_per_day: Optional[int] = None
    request_interval_seconds: Optional[int] = None
    first_step_config_type: Optional[FirstStepConfigEnum] = None
    is_default: Optional[bool] = None


class LinkedinConfigStepStatusResponse(BaseModel):
    is_message_limit_done: Optional[bool] = None
    is_connect_limit_done: Optional[bool] = None
    is_view_profile_limit_done: Optional[bool] = None
    is_request_interval_done: Optional[bool] = None


class LinkedInAccountBase(BaseModel):
    id: int
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    account_name: Optional[str] = None
    public_identifier: Optional[str] = None
    account_type: Optional[str] = None
    status: Optional[LinkedInAccountStatus]
    account_id: Optional[str] = None
    messages_sent_per_day: Optional[int] = None
    messages_sent_per_week: Optional[int] = None
    connections_sent_per_day: Optional[int] = None
    connections_sent_per_week: Optional[int] = None
    profile_views_per_day: Optional[int] = None
    is_default: Optional[bool] = None
    config_step_status: Optional[LinkedinConfigStepStatusResponse] = None
    is_current_user: Optional[bool] = None
    request_interval_seconds: Optional[int] = None


class SimpleLinkedinSenderResponse(BaseModel):
    id: int
    account_name: Optional[str]
    public_identifier: Optional[str]


class ListLinkedinSenderResponse(BaseModel):
    data: List[SimpleLinkedinSenderResponse]
