from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, TIMESTAMP, Column, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class Contact(SQLModel, table=True):
    __tablename__: str = "contacts"

    id: Optional[int] = Field(default=None, primary_key=True)
    person_uuid: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None, unique=True
    )
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    corporate_number: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(64))), default=None
    )
    name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    bio: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    email: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    address: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    skills: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
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
    lead_source_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    status_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    company_name: Optional[str] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    potential_action_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    site_usage_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    change_history_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    tags: Optional[List[str]] = Field(
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
