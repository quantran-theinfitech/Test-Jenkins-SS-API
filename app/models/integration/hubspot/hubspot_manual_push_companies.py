from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, String, Text, func
from sqlmodel import Field, SQLModel


class HubspotManualPushCompanies(SQLModel, table=True):
    __tablename__: str = "hubspot_manual_push_companies"
    id: Optional[int] = Field(default=None, primary_key=True)
    log_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(50)), default=None
    )
    company_id: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
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
