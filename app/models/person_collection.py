import enum
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import ARRAY, JSON, TIMESTAMP, Column, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class StatusCode(str, enum.Enum):
    Draft = "DRAFT"
    Open = "OPEN"
    Archive = "ARCHIVE"


class TypeCode(str, enum.Enum):
    CSV = "CSV"
    SYS = "SYS"


class PersonCollection(SQLModel, table=True):
    __tablename__: str = "person_collections"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    group_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    description: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    status_code: Optional[StatusCode]
    search_condition: Dict = Field(nullable=True, sa_column=Column(JSON), default=None)
    step: Optional[int] = Field(nullable=True, sa_column=Column(Integer), default=None)
    type_code: Optional[TypeCode]
    tags: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
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
