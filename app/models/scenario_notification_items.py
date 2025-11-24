from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, String, func
from sqlmodel import Field, SQLModel


class ScenarioNotificationItems(SQLModel, table=True):
    __tablename__: str = "scenario_notification_items"
    id: Optional[int] = Field(default=None, primary_key=True)
    scenario_notification_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    media_internal_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(256)), default=None
    )
    media_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
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
