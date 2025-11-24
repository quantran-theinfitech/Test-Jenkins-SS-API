from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, func
from sqlmodel import Field, SQLModel


class SequenceCampaignScheduleSendingWindows(SQLModel, table=True):
    __tablename__: str = "sequence_campaign_schedule_sending_windows"
    id: Optional[int] = Field(default=None, primary_key=True)
    schedule_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    start_time: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    end_time: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    week_day: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
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
