import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, String, Text, func
from sqlmodel import Enum, Field, SQLModel


class ContentType(str, enum.Enum):
    MAIL = "MAIL"
    MESSAGE = "MESSAGE"
    NOTE = "NOTE"


class SequenceStepContentTemplate(SQLModel, table=True):
    __tablename__: str = "sequence_step_content_templates"
    id: Optional[int] = Field(default=None, primary_key=True)
    content: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    title: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
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
    external_mautic_mail_template_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    is_reply_to_previous_thread: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=False
    )
    is_include_signature: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=False
    )
    content_type: Optional[ContentType] = Field(
        default=None, sa_column=Column(Enum(ContentType), nullable=True)
    )
