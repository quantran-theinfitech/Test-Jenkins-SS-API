from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, SmallInteger, String, func
from sqlmodel import Field, SQLModel


class TrackingUrl(SQLModel, table=True):
    __tablename__: str = "tracking_urls"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    original_url: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    shorten_path: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    tracking_flag: Optional[int] = Field(
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
