from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, String, func
from sqlmodel import Field, Index, SQLModel


class HubspotCompanyPushHistories(SQLModel, table=True):
    __tablename__: str = "hubspot_company_push_histories"
    __table_args__ = (Index("idx_hubspot_company_push_histories_id", "id"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    ss_company_id: Optional[int] = Field(
        default=None, nullable=True, sa_column=Column(Integer)
    )
    error_type: Optional[str] = Field(
        default=None, nullable=True, sa_column=Column(String(50))
    )
    log_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(50)), default=None
    )
    created_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    deleted_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
