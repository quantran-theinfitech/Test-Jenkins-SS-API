from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, TIMESTAMP, Boolean, Column, Enum, Integer, String, func
from sqlmodel import Field, SQLModel

from app.models.sequence.contact import SequencePersonStage


class SequenceCampaignSetting(SQLModel, table=True):
    __tablename__: str = "sequence_campaign_settings"
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
    sequence_campaign_id: int = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    days_until_unresponsive: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    stage_list_as_not_sent: Optional[List[SequencePersonStage]] = Field(
        nullable=True, sa_column=Column(ARRAY(Enum(SequencePersonStage))), default=None
    )
    is_finished_when_replied: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
    is_finished_when_unsubscribed: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
    is_status_change_when_bounced: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
    cc_list: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    bcc_list: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
