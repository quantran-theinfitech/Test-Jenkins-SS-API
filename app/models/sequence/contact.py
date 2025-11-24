import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, TIMESTAMP, Column, Enum, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class SequencePersonStage(str, enum.Enum):
    COLD = "COLD"
    APPROACHING = "APPROACHING"
    BAD_DATA = "BAD_DATA"
    DO_NOT_CONTACT = "DO_NOT_CONTACT"
    REPLIED = "REPLIED"
    UNRESPONSIVE = "UNRESPONSIVE"


class ContactType(str, enum.Enum):
    PERSON = "PERSON"
    COMPANY = "COMPANY"


class SequenceContact(SQLModel, table=True):
    __tablename__: str = "sequence_contacts"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    sequence_campaign_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    target_type: Optional[str] = Field(
        nullable=True, sa_column=Column(Enum(ContactType))
    )
    name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    role_name: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(Text)), default=None
    )
    email: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    linkedin_url: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    twitter_url: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    github_url: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    note_url: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    fb_url: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    wantedly_url: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    skills: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    corporate_number: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(64))), default=None
    )
    status: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    current_step: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    stage: Optional[SequencePersonStage] = Field(
        nullable=True, sa_column=Column(Enum(SequencePersonStage)), default=None
    )
    company_name: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    wantedly_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    address: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    linkedin_internal_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    intro: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    bio: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    role_code: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    role_group_codes: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
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
