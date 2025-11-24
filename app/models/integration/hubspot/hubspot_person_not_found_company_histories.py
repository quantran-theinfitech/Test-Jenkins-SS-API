from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, String, func
from sqlmodel import Field, SQLModel


class HubspotPersonNotFoundHubspotCompanyHistories(SQLModel, table=True):
    __tablename__: str = "hubspot_person_not_found_hubspot_company_histories"
    id: Optional[int] = Field(default=None, primary_key=True)
    hubspot_person_log_id: Optional[int] = Field(
        default=None, nullable=True, sa_column=Column(Integer)
    )
    ss_company_id: Optional[str] = Field(
        default=None, sa_column=Column(String(255), nullable=True)
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
