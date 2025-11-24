import enum
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import JSON, TIMESTAMP, Column, Integer, String, func
from sqlmodel import Field, SQLModel


class OwnerCodeCondition(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class SearchCondition(SQLModel, table=True):
    __tablename__: str = "search_conditions"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    owner_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    conditions: Dict = Field(nullable=True, sa_column=Column(JSON), default=None)
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
