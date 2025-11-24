from datetime import datetime
from typing import Optional

from sqlmodel import TIMESTAMP, Column, Field, Integer, SQLModel, String, Text, func


class HubspotCompanySyncHistories(SQLModel, table=True):
    __tablename__: str = "hubspot_company_sync_histories"
    id: Optional[int] = Field(default=None, primary_key=True)
    log_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(50)), default=None
    )
    integration_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    hubspot_team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    hubspot_push_type: Optional[str] = Field(
        nullable=True, sa_column=Column(String(50)), default=None
    )
    type: Optional[str] = Field(
        nullable=True, sa_column=Column(String(50)), default=None
    )
    total_companies: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    error_message: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    status: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    sync_count: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
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
