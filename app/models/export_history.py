import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Enum, Integer, String, func
from sqlmodel import Field, SQLModel


class ExportType(str, enum.Enum):
    CPN = "CPN"
    PERSON = "PERSON"


class ExportStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    CREDIT_ERROR = "CREDIT_ERROR"


class ExportHistory(SQLModel, table=True):
    __tablename__: str = "export_histories"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
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
    amount: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    file_name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    export_type: Optional[ExportType] = Field(
        nullable=True,
        sa_column=Column(Enum(ExportType), default=None),
    )
    status: Optional[ExportStatus] = Field(
        nullable=True,
        sa_column=Column(Enum(ExportStatus), default=None),
    )
