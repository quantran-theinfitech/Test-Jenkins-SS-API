import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Enum, Integer, String, func
from sqlalchemy.dialects.postgresql import TEXT
from sqlmodel import Field, SQLModel


class FormJobItemStatusCode(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    QUEUED = "QUEUED"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    NOT_SEND = "NOT_SEND"


class FormJobItem(SQLModel, table=True):
    __tablename__: str = "form_job_items"
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    corporate_number: Optional[str] = Field(
        nullable=True, sa_column=Column(String), default=None
    )
    company_custom_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    form_url: Optional[str] = Field(nullable=True, sa_column=Column(TEXT), default=None)
    status_code: Optional[FormJobItemStatusCode] = Field(
        nullable=True, sa_column=Column(Enum(FormJobItemStatusCode)), default=None
    )
    aws_batch_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String), default=None
    )
    retry_count: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=0
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
    started_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    ended_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
