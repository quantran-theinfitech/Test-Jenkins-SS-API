from datetime import datetime
from typing import List, Optional

from sqlmodel import (
    ARRAY,
    TIMESTAMP,
    Boolean,
    Column,
    Field,
    Integer,
    SQLModel,
    String,
    func,
)


class FormSchedule(SQLModel, table=True):
    __tablename__: str = "form_schedules"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    time_zone: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    is_skip_holiday: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
    is_default: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
    days_per_week: Optional[List[int]] = Field(
        nullable=True, sa_column=Column(ARRAY(Integer)), default=None
    )
    team_id: Optional[int] = Field(
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
    deleted_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    deleted_by: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
