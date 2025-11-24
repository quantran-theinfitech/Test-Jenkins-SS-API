from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import JSON, TIMESTAMP, Column, Integer, String, func
from sqlmodel import Field, SQLModel


class TeamSetting(SQLModel, table=True):
    __tablename__: str = "team_settings"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    setting_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    value: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    label: Optional[str] = Field(nullable=True, sa_column=Column(String), default=None)
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
