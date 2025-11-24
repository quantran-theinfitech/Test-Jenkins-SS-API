from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import JSON, TIMESTAMP, Column, Integer, String, UniqueConstraint, func
from sqlmodel import Field, SQLModel


class HubspotRawCompanies(SQLModel, table=True):
    __tablename__: str = "hubspot_raw_companies"
    __table_args__ = (
        UniqueConstraint(
            "hubspot_team_id",
            "integration_id",
            "hubspot_company_id",
            name="hubspot_raw_companies_unique_key",
        ),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    hubspot_team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    integration_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    hubspot_company_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(50)), default=None
    )
    data: Optional[Dict] = Field(
        nullable=True, sa_column=Column("data", JSON), default=None
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
