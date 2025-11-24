import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, String, func
from sqlmodel import Field, SQLModel


class StatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSE = "PAUSE"
    FINISH = "FINISH"
    BOUNCED = "BOUNCED"
    NOT_SENT = "NOT_SENT"


class SequenceCampaignContacts(SQLModel, table=True):
    __tablename__: str = "sequence_campaign_contacts"

    id: Optional[int] = Field(default=None, primary_key=True)
    sequence_campaign_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    sequence_contact_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    status: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    reason: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    time_resumed: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, nullable=True)
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
