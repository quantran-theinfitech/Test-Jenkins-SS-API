import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Boolean, Column, Enum, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class MailHistoryBounceType(str, enum.Enum):
    PERMANENT = "PERMANENT"
    TRANSIENT = "TRANSIENT"
    UNDETERMINED = "UNDETERMINED"


class MailHistoryBounceSubType(str, enum.Enum):
    GENERAL = "GENERAL"
    NO_EMAIL = "NO_EMAIL"
    SUPPRESSED = "SUPPRESSED"
    ON_ACCOUNT_SUPPRESSION_LIST = "ON_ACCOUNT_SUPPRESSION_LIST"
    MESSAGE_TOO_LARGE = "MESSAGE_TOO_LARGE"
    MAILBOX_FULL = "MAILBOX_FULL"
    CONTENT_REJECTED = "CONTENT_REJECTED"
    ATTACHMENT_REJECTED = "ATTACHMENT_REJECTED"
    UNDETERMINED = "UNDETERMINED"


class MailHistoryStatus(str, enum.Enum):
    SENT = "SENT"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    SCHEDULED = "SCHEDULED"
    OPENED = "OPENED"
    DRAFT = "DRAFT"
    REPLIED = "REPLIED"
    BOUNCED = "BOUNCED"
    OPT_OUT = "OPT_OUT"
    NOT_SENT = "NOT_SENT"


class MailHistoryProcessStatus(str, enum.Enum):
    PENDING = "PENDING"
    PERSON_PAUSED = "PERSON_PAUSED"
    MAILBOX_NOT_FOUND = "MAILBOX_NOT_FOUND"
    LINKEDIN_ACCOUNT_NOT_FOUND = "LINKEDIN_ACCOUNT_NOT_FOUND"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class AccountOption(str, enum.Enum):
    MANUAL = "MANUAL"
    DEFAULT = "DEFAULT"


class FailCode(str, enum.Enum):
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    TEAM_NOT_FOUND = "TEAM_NOT_FOUND"
    EMAIL_NOT_FOUND = "EMAIL_NOT_FOUND"
    NOT_ENOUGH_EMAIL_CREDIT = "NOT_ENOUGH_EMAIL_CREDIT"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    CANNOT_INVITE_ATTENDEE = "CANNOT_INVITE_ATTENDEE"
    CANNOT_RESEND_YET = "CANNOT_RESEND_YET"
    ALREADY_INVITED_RECENTLY = "ALREADY_INVITED_RECENTLY"
    INSUFFICIENT_CREDITS = "INSUFFICIENT_CREDITS"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    RECIPIENT_LINKEDIN_ACCOUNT_NOT_FOUND = "RECIPIENT_LINKEDIN_ACCOUNT_NOT_FOUND"
    LINKEDIN_SENDER_NOT_FOUND = "LINKEDIN_SENDER_NOT_FOUND"
    NOT_ENOUGH_LINKEDIN_CREDIT = "NOT_ENOUGH_LINKEDIN_CREDIT"
    ACCOUNT_RECONNECT_REQUIRED = "ACCOUNT_RECONNECT_REQUIRED"


MAIL_HISTORY_VIEW_NAME = "mail_history_with_next_step_schedule_view"


class SequenceMailHistory(SQLModel, table=True):
    __tablename__: str = "sequence_mail_histories"
    id: Optional[int] = Field(default=None, primary_key=True)
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
    sequence_mailbox_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    sequence_linkedin_account_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    sequence_contact_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    sequence_step_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    sequence_campaign_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    title: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    content: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    to_address: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    status: Optional[MailHistoryStatus] = Field(
        nullable=True, sa_column=Column(Enum(MailHistoryStatus)), default=None
    )
    process_status: Optional[MailHistoryProcessStatus] = Field(
        nullable=True, sa_column=Column(Enum(MailHistoryProcessStatus)), default=None
    )
    sent_at: Optional[datetime] = Field(
        nullable=True, sa_column=Column(TIMESTAMP), default=None
    )
    sent_by: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    next_sequence_step_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    tracking_token: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    thread_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    delivered_at: Optional[datetime] = Field(
        nullable=True, sa_column=Column(TIMESTAMP), default=None
    )
    opened_at: Optional[datetime] = Field(
        nullable=True, sa_column=Column(TIMESTAMP), default=None
    )
    replied_at: Optional[datetime] = Field(
        nullable=True, sa_column=Column(TIMESTAMP), default=None
    )
    bounced_at: Optional[datetime] = Field(
        nullable=True, sa_column=Column(TIMESTAMP), default=None
    )
    bounce_type: Optional[MailHistoryBounceType] = Field(
        nullable=True, sa_column=Column(Enum(MailHistoryBounceType)), default=None
    )
    bounce_sub_type: Optional[MailHistoryBounceSubType] = Field(
        nullable=True, sa_column=Column(Enum(MailHistoryBounceSubType)), default=None
    )
    diag_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    mailbox_alias_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    is_include_opt_out_and_signature: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=False
    )
    is_rescheduled: Optional[bool] = Field(
        nullable=True, sa_column=Column(Boolean), default=False
    )
    email_signature: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    opt_out_message: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    account_option: Optional[AccountOption] = Field(
        nullable=True,
        sa_column=Column(Enum(AccountOption)),
        default=AccountOption.DEFAULT,
    )
    fail_reason: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
