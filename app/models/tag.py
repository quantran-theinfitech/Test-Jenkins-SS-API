import enum
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import TIMESTAMP, Column, Integer, String, func
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, SQLModel


class ModelCode(str, enum.Enum):
    Cpn = "CPN"
    Rec = "REC"
    Keyman = "KEYMAN"


class Tag(SQLModel, table=True):
    __tablename__: str = "tags"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    model_code: Optional[ModelCode]
    model_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    metadata_: Dict = Field(
        nullable=True, sa_column=Column("metadata", JSON), default={}
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
