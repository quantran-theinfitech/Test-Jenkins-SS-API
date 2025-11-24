import enum
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import JSON, TIMESTAMP, Column, Enum, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class ModelCode(str, enum.Enum):
    TODO = ("TODO",)
    FORM = ("FORM",)
    MAIL = "MAIL"


class ActivityLog(SQLModel, table=True):
    __tablename__: str = "activity_logs"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    corporate_number: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    model_code: Optional[ModelCode] = Field(
        default=None, sa_column=Column(Enum(ModelCode), nullable=True)
    )
    model_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    metadata_: Dict = Field(
        nullable=True, sa_column=Column("metadata", JSON), default={}
    )
    status_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    memo: Optional[str] = Field(default=None, sa_column=Column(Text), nullable=True)
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
