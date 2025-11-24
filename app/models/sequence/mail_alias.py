from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class SequenceMailAlias(SQLModel, table=True):
    __tablename__: str = "sequence_mail_aliases"
    id: Optional[int] = Field(default=None, primary_key=True)
    sequence_mailbox_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    alias_email: Optional[str] = Field(
        nullable=True, sa_column=Column(String(128)), default=None
    )
    alias_name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(128)), default=None
    )
    alias_signature: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    is_default: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
    is_primary: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
    created_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
