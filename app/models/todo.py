import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class StatusCode(str, enum.Enum):
    Pending = "PENDING"
    Done = "DONE"


class Todo(SQLModel, table=True):
    __tablename__: str = "todos"
    id: Optional[int] = Field(default=None, primary_key=True)
    corporate_number: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    assignee_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    title: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    content: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    memo: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    plan_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    customer_name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    status_code: Optional[StatusCode]
    type_code: Optional[str] = Field(
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
