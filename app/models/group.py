from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, SmallInteger, String, Text, func
from sqlmodel import Field, SQLModel


class Group(SQLModel, table=True):
    __tablename__: str = "groups"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    description: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    default_flag: Optional[int] = Field(
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
