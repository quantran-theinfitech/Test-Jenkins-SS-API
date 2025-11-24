import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Enum, String, Text, UniqueConstraint, func
from sqlmodel import Field, Index, SQLModel


class TypeCode(str, enum.Enum):
    EXPO = "EXPO"
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"


class Event(SQLModel, table=True):
    __tablename__: str = "events"

    __table_args__ = (
        UniqueConstraint("media_code", "media_internal_id", name="events_unique_id"),
        Index("idx_event_corporate_number", "corporate_number"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    source_event_url: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )

    media_internal_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )

    media_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )

    tool: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )

    corporate_number: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )

    ingest_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )

    name: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)

    content: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)

    image: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)

    start_time: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )

    end_time: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )

    type: Optional[TypeCode] = Field(
        default=None, sa_column=Column(Enum(TypeCode), nullable=True)
    )

    address: Optional[str] = Field(nullable=True, default=None)

    created_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )

    updated_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
