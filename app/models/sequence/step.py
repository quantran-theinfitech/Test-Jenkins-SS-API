import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Boolean, Column, Enum, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class StepType(str, enum.Enum):
    MAIL_MANUAL = "MAIL_MANUAL"
    MAIL_AUTO = "MAIL_AUTO"
    LINKEDIN_CONNECTION_REQUEST = "LINKEDIN_CONNECTION_REQUEST"
    LINKEDIN_AUTO_MESSAGE = "LINKEDIN_AUTO_MESSAGE"
    LINKEDIN_VIEW_PROFILE = "LINKEDIN_VIEW_PROFILE"


class TimingType(str, enum.Enum):
    IMMEDIATE = "IMMEDIATE"
    SCHEDULED = "SCHEDULED"


class ScheduleUnit(str, enum.Enum):
    DAYS = "DAYS"
    HOURS = "HOURS"
    MINUTES = "MINUTES"


class Priority(str, enum.Enum):
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class FallbackMessageAction(str, enum.Enum):
    SKIP = "SKIP"
    INMAIL = "INMAIL"


class SequenceCampaignStep(SQLModel, table=True):
    __tablename__: str = "sequence_campaign_steps"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    created_by: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    updated_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_by: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    deleted_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    deleted_by: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    title: str = Field(nullable=False, sa_column=Column(Text))
    step_type: Optional[StepType] = Field(
        default=None, sa_column=Column(Enum(StepType), nullable=True)
    )
    description: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    sequence_campaign_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    timing_type: Optional[TimingType] = Field(
        default=None, sa_column=Column(Enum(TimingType), nullable=True)
    )
    schedule_unit: Optional[ScheduleUnit] = Field(
        default=None, sa_column=Column(Enum(ScheduleUnit), nullable=True)
    )
    schedule_value: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    priority: Optional[Priority] = Field(
        default=None, sa_column=Column(Enum(Priority), nullable=True)
    )
    memo: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    is_email_limit_enabled: bool = Field(sa_column=Column(Boolean), default=False)
    email_limit_count: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    is_skip_enabled: bool = Field(sa_column=Column(Boolean), default=False)
    skip_after_days: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    content_template_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    is_active: bool = Field(sa_column=Column(Boolean), default=True)
    activated_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP))
    order: int = Field(sa_column=Column(Integer), default=0)
    uuid: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    total_days: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    fallback_message_action: Optional[FallbackMessageAction] = Field(
        default=None, sa_column=Column(Enum(FallbackMessageAction), nullable=True)
    )
