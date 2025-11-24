import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Enum, Integer, String, Text, func
from sqlmodel import Field, SQLModel

from app.models.sequence.mail_history import AccountOption
from app.models.sequence.step import Priority


class TaskType(str, enum.Enum):
    EMAIL = "EMAIL"
    CALL = "CALL"
    ACTION_ITEM = "ACTION_ITEM"


class TaskStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLTETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class SequenceTask(SQLModel, table=True):
    __tablename__: str = "sequence_tasks"
    id: Optional[int] = Field(default=None, primary_key=True)
    sequence_person_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    user_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    sequence_campaign_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    sequence_step_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    task_type: Optional[TaskType] = Field(
        nullable=True, sa_column=Column(Enum(TaskType)), default=None
    )
    sequence_linkedin_account_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    account_option: Optional[AccountOption] = Field(
        nullable=True,
        sa_column=Column(Enum(AccountOption)),
        default=AccountOption.DEFAULT,
    )
    priority: Optional[Priority] = Field(
        nullable=True, sa_column=Column(Enum(Priority)), default=None
    )
    title: Optional[str] = Field(
        nullable=True, sa_column=Column(String(128)), default=None
    )
    description: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    due_date: Optional[datetime] = Field(
        nullable=True, sa_column=Column(TIMESTAMP), default=None
    )
    status: Optional[TaskStatus] = Field(
        nullable=True, sa_column=Column(Enum(TaskStatus)), default=None
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
