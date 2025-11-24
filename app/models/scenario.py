from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from sqlalchemy import JSON, TIMESTAMP, Column, Integer, String, Text, func
from sqlmodel import Boolean, Field, SQLModel


class TypeCode(str, Enum):
    RECRUIT = "RECRUIT"
    NEWS = "NEWS"
    TECH = "TECH"


class Scenario(SQLModel, table=True):
    __tablename__: str = "scenarios"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    type_code: Optional[TypeCode] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    trigger_conditions: Optional[Dict] = Field(
        nullable=True, sa_column=Column("trigger_conditions", JSON), default=None
    )
    description: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    target_email: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    target_slack_connection_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    email_notification_flag: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
    slack_notification_flag: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
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
