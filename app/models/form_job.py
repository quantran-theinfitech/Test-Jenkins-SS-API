import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Enum, Integer, SmallInteger, String, func
from sqlmodel import Field, SQLModel


class FormJobStatusCode(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"


class FormJobTypeCode(str, enum.Enum):
    SYS = "SYS"
    CSV = "CSV"


class FormJob(SQLModel, table=True):
    __tablename__: str = "form_jobs"
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
    type_code: Optional[FormJobTypeCode] = Field(
        nullable=True, sa_column=Column(Enum(FormJobTypeCode)), default=None
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
    form_schedule_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    status_code: Optional[FormJobStatusCode] = Field(
        default=None, sa_column=Column(Enum(FormJobStatusCode), nullable=True)
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
