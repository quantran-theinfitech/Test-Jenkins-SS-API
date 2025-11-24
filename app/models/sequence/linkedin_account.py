import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlmodel import Boolean, Field, SQLModel, String


class LinkedInAccountStatus(str, enum.Enum):
    CREATION_SUCCESS = "CREATION_SUCCESS"
    RECONNECTED = "RECONNECTED"
    CREDENTIALS = "CREDENTIALS"
    CONNECTING = "CONNECTING"
    OK = "OK"
    ERROR = "ERROR"
    STOPPED = "STOPPED"
    SYNC_SUCCESS = "SYNC_SUCCESS"
    DELETED = "DELETED"


class FirstStepConfigEnum(str, enum.Enum):
    NEW_ACCOUNT = "NEW_ACCOUNT"
    PAID_OR_ACTIVE_ACCOUNT = "PAID_OR_ACTIVE_ACCOUNT"
    LATEST_SETTINGS = "LATEST_SETTINGS"


class LinkedInAccount(SQLModel, table=True):
    __tablename__: str = "linkedin_accounts"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    account_name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(128)), default=None
    )
    public_identifier: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    account_type: Optional[str] = Field(
        nullable=True, sa_column=Column(String(128)), default=None
    )
    status: Optional[LinkedInAccountStatus] = Field(
        default=None,
        nullable=True,
        sa_column=Column(
            ENUM(
                LinkedInAccountStatus,  # enum class
                name="linkedinaccountstatus",  # tên kiểu enum trong PostgreSQL
                create_type=False,  # tránh Alembic tự tạo nếu enum đã có
            )
        ),
    )
    account_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(128)), default=None
    )
    messages_sent_per_day: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    messages_sent_per_week: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    connections_sent_per_day: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    connections_sent_per_week: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    profile_views_per_day: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    request_interval_seconds: Optional[int] = Field(
        default=60, nullable=True, sa_column=Column(Integer, server_default="60")
    )
    is_default: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
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
