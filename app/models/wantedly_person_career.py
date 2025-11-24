from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class WantedlyPersonCareer(SQLModel, table=True):
    __tablename__: str = "wantedly_person_careers"
    id: Optional[int] = Field(default=None, primary_key=True)
    person_uuid: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    company_name: Optional[str] = Field(
        default=None, sa_column=Column(String(255)), nullable=True
    )
    role_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    role_name: Optional[str] = Field(
        default=None, sa_column=Column(String(255)), nullable=True
    )
    description: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    start_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    end_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
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
