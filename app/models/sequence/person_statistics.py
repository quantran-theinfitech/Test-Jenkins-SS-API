import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, func
from sqlmodel import Field, SQLModel


class SequencePersonStage(str, enum.Enum):
    COLD = "COLD"
    APPROACHING = "APPROACHING"
    BAD_DATA = "BAD_DATA"
    DO_NOT_CONTACT = "DO_NOT_CONTACT"
    REPLIED = "REPLIED"
    UNRESPONSIVE = "UNRESPONSIVE"


class SequencePersonStatistics(SQLModel, table=True):
    __tablename__: str = "sequence_person_statistics"

    id: Optional[int] = Field(default=None, primary_key=True)
    sequence_person_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    last_activity: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    email_last_opened_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    email_last_clicked_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    times_opened: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    times_clicked: Optional[int] = Field(
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
    deleted_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    deleted_by: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
