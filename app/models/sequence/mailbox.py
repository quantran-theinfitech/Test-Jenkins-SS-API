import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    TIMESTAMP,
    Boolean,
    Column,
    Enum,
    Integer,
    String,
    Text,
    func,
)
from sqlmodel import Field, SQLModel


class MailboxType(str, enum.Enum):
    SMTP = "SMTP"
    GOOGLE_API = "GOOGLE_API"


class SequenceMailbox(SQLModel, table=True):
    __tablename__: str = "sequence_mailboxes"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    mailbox_type: Optional[MailboxType] = Field(
        nullable=True, sa_column=Column(Enum(MailboxType)), default=None
    )
    email: Optional[str] = Field(
        nullable=True, sa_column=Column(String(128)), default=None
    )
    password: Optional[str] = Field(
        nullable=True, sa_column=Column(String(128)), default=None
    )
    host: Optional[str] = Field(
        nullable=True, sa_column=Column(String(128)), default=None
    )
    port: Optional[int] = Field(nullable=True, sa_column=Column(Integer), default=None)
    imap_email: Optional[str] = Field(
        nullable=True, sa_column=Column(String(128)), default=None
    )
    imap_password: Optional[str] = Field(
        nullable=True, sa_column=Column(String(128)), default=None
    )
    imap_host: Optional[str] = Field(
        nullable=True, sa_column=Column(String(128)), default=None
    )
    imap_port: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    emails_sent_per_day: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    emails_sent_per_hour: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    email_signature: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    opt_out_message_after_signature: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    is_opt_out_message_after_signature: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
    is_open_tracking: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
    is_click_tracking: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
    is_include_one_click_unsubscribe_headers: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
    )
    google_refresh_token: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    config_step_done: Optional[List[int]] = Field(
        nullable=True, sa_column=Column(ARRAY(Integer)), default=None
    )
    is_default: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=None
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
