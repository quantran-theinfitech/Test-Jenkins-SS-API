from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    TIMESTAMP,
    Column,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlmodel import Field, Index, SQLModel


class Person(SQLModel, table=True):
    __tablename__: str = "persons"

    __table_args__ = (
        UniqueConstraint("uuid", name="person_unique_uuid"),
        Index("idx_person_corporate_number", "corporate_number"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
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
    company_name: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    wantedly_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    address: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    prefecture_name: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    linkedin_internal_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    intro: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    bio: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    role_code: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    role_group: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    role_group_codes: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    sub_group_codes: Optional[List[str]] = Field(
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
