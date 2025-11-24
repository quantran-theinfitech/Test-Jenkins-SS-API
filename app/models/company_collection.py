import enum
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import JSON, TIMESTAMP, Column, Integer, String, func
from sqlalchemy.dialects.postgresql import TEXT
from sqlmodel import Field, SQLModel


class ModeCode(str, enum.Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class StatusCode(str, enum.Enum):
    Draft = "DRAFT"
    Open = "OPEN"
    Archive = "ARCHIVE"


class TypeCode(str, enum.Enum):
    CSV = "CSV"
    SYS = "SYS"


class CompanyCollection(SQLModel, table=True):
    __tablename__: str = "company_collections"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    group_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    description: Optional[str] = Field(
        nullable=True, sa_column=Column(TEXT), default=None
    )
    status_code: Optional[StatusCode]
    search_condition: Optional[Dict] = Field(
        nullable=True, sa_column=Column("search_condition", JSON), default=None
    )
    step: Optional[int] = Field(nullable=True, sa_column=Column(Integer), default=None)
    type_code: Optional[TypeCode] = None
    csv_path: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    mode_code: Optional[ModeCode] = Field(
        nullable=True, sa_column=Column(String[10]), default=ModeCode.AUTO
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
