from datetime import datetime
from typing import Optional

from sqlmodel import TIMESTAMP, Column, Field, Integer, SQLModel, func


class FormScheduleSendingWindow(SQLModel, table=True):
    __tablename__: str = "form_schedule_sending_windows"
    id: Optional[int] = Field(default=None, primary_key=True)
    form_schedule_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    start_time: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    end_time: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    week_day: Optional[int] = Field(
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
