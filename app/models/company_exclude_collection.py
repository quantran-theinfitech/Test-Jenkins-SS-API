import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Float, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class TypeCode(str, enum.Enum):
    CSV = "CSV"
    SYS = "SYS"


class StatusCode(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class CompanyExcludeCollection(SQLModel, table=True):
    __tablename__: str = "company_exclude_collections"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    description: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    type_code: Optional[TypeCode]
    status_code: Optional[StatusCode]
    identification_rate: float = Field(
        nullable=True, sa_column=Column(Float), default=None
    )
    csv_path: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
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
