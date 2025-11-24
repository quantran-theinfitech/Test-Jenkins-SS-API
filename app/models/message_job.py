from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, SmallInteger, String, Text, func
from sqlmodel import Field, SQLModel


class MessageJob(SQLModel, table=True):
    __tablename__: str = "message_jobs"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    collection_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    platform_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    account_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    content: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    exclude_keyman_collection_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    schedule_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    connection_only_flag: Optional[int] = Field(
        nullable=True, sa_column=Column(SmallInteger), default=None
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
