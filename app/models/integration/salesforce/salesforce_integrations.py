from datetime import datetime
from typing import Optional

from sqlmodel import (
    TIMESTAMP,
    Boolean,
    Column,
    Field,
    Integer,
    SQLModel,
    String,
    Text,
    func,
)


class SalesforceIntegrations(SQLModel, table=True):
    __tablename__: str = "salesforce_integrations"
    id: Optional[int] = Field(default=None, primary_key=True)
    salesforce_team_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    email: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    code: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    instance_url: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    id_url: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    access_token: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    refresh_token: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    auto_pull_companies: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    auto_pull_persons: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    auto_sync_companies: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    created_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    deleted_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
