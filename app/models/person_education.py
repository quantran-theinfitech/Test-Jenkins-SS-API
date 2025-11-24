from datetime import datetime
from typing import Optional

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlmodel import Field, SQLModel


class PersonEducation(SQLModel, table=True):
    __tablename__: str = "person_educations"

    __table_args__ = (
        UniqueConstraint(
            "person_uuid",
            "education_id",
            "media_code",
            name="person_education_unique_key",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    person_uuid: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    education_id: Optional[str] = Field(
        default=None, sa_column=Column(String(255)), nullable=True
    )
    school_name: Optional[str] = Field(
        default=None, sa_column=Column(String(255)), nullable=True
    )
    major: Optional[str] = Field(
        default=None, sa_column=Column(String(255)), nullable=True
    )
    description: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    media_code: Optional[str] = Field(
        default=None, sa_column=Column(String(20)), nullable=True
    )
    start_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    end_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    current_flag: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
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
