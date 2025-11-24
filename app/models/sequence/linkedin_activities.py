import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Boolean, Column, Enum, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class LinkedinHistoryStatus(str, enum.Enum):
    SENT = "SENT"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    SCHEDULED = "SCHEDULED"
    OPENED = "OPENED"
    DRAFT = "DRAFT"
    REPLIED = "REPLIED"
    BOUNCED = "BOUNCED"
    OPT_OUT = "OPT_OUT"


class LinkedinHistoryProcessStatus(str, enum.Enum):
    PENDING = "PENDING"
    PERSON_PAUSED = "PERSON_PAUSED"
    LINKEDIN_ACCOUNT_NOT_FOUND = "LINKEDIN_ACCOUNT_NOT_FOUND"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ExecutorOption(str, enum.Enum):
    CURRENT_STEP = "CURRENT_STEP"
    ALL_FOLLOWING_STEPS = "ALL FOLLOWING STEPS"


class SequenceLinkedinActivities(SQLModel, table=True):
    __tablename__: str = "sequence_linkedin_activities"
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
    sequence_campaign_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    sequence_step_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    sequence_person_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    linkedin_account_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    thread_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    message: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    status: Optional[LinkedinHistoryStatus] = Field(
        nullable=True, sa_column=Column(Enum(LinkedinHistoryStatus)), default=None
    )
    process_status: Optional[LinkedinHistoryProcessStatus] = Field(
        nullable=True,
        sa_column=Column(Enum(LinkedinHistoryProcessStatus)),
        default=None,
    )
    next_sequence_step_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    executor_option: Optional[ExecutorOption] = Field(
        nullable=True, sa_column=Column(Enum(ExecutorOption)), default=None
    )
    sent_at: Optional[datetime] = Field(
        nullable=True, sa_column=Column(TIMESTAMP), default=None
    )
    sent_by: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    replied_at: Optional[datetime] = Field(
        nullable=True, sa_column=Column(TIMESTAMP), default=None
    )
    is_rescheduled: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=False
    )
    tracking_token: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
