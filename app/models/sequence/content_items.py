import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class ContentItemsType(str, enum.Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    FILE = "FILE"


class SequenceStepContentItem(SQLModel, table=True):
    __tablename__: str = "sequence_step_content_items"
    id: Optional[int] = Field(default=None, primary_key=True)
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
    step_content_template_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    type: Optional[ContentItemsType] = Field(
        nullable=True, sa_column=Column(String(255), default=None)
    )
    mime_type: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    content: Optional[str] = Field(default=None, sa_column=Column(Text), nullable=True)
    file_path: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    file_name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255), default=None)
    )
    order: Optional[int] = Field(nullable=True, sa_column=Column(Integer), default=None)
