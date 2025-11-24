from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, String, func
from sqlmodel import Field, SQLModel


class CompanyContact(SQLModel, table=True):
    __tablename__: str = "company_contacts"
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    email: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    tel: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    gender_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    role: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    department: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
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
