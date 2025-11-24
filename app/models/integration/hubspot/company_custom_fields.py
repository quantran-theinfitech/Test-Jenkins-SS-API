from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, String, func
from sqlmodel import Field, SQLModel


class CompanyCustomFields(SQLModel, table=True):
    __tablename__: str = "company_custom_fields"
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    company_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    field: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    value: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    created_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    deleted_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
