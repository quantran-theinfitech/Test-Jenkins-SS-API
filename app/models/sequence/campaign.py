from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, String, func
from sqlmodel import Field, SQLModel


class SequenceCampaign(SQLModel, table=True):
    __tablename__: str = "sequence_campaigns"
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
    name: str = Field(nullable=False, sa_column=Column(String(255)))
    is_active: bool = Field(sa_column=Column(Boolean), default=False)
    is_first_active: bool = Field(sa_column=Column(Boolean), default=False)
    activated_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP))
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    owner_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    schedule_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
