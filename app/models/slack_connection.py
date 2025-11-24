from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, String, func
from sqlmodel import Field, SQLModel


class SlackConnection(SQLModel, table=True):
    __tablename__: str = "slack_connections"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    workspace_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    workspace_name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    channel_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    channel_name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    url: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
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
