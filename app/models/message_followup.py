from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import JSON, TIMESTAMP, Column, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class MessageFollowup(SQLModel, table=True):
    __tablename__: str = "message_followup"
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    content: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    trigger_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    trigger_value: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    priority: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    metadata_: Dict = Field(
        nullable=True, sa_column=Column("metadata", JSON), default=None
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
