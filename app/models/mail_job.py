import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Enum, Integer, SmallInteger, String, func
from sqlmodel import Field, SQLModel


class MailJobStatusCode(str, enum.Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING_SUCCESS = "RUNNING_SUCCESS"
    RUNNING_ERROR = "RUNNING_ERROR"
    DONE_SUCCESS = "DONE_SUCCESS"
    DONE_ERROR = "DONE_ERROR"


class MailJob(SQLModel, table=True):
    __tablename__: str = "mail_jobs"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    template_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    placeholder_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    target_collection_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    exclude_collection_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    approach_ng_flag: Optional[int] = Field(
        nullable=True, sa_column=Column(SmallInteger), default=None
    )
    schedule_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    max_resend_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    status_code: Optional[MailJobStatusCode] = Field(
        default=None, sa_column=Column(Enum(MailJobStatusCode), nullable=True)
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
