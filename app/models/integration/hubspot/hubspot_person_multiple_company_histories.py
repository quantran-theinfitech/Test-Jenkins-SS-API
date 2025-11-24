from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, TIMESTAMP, Column, Integer, String, func
from sqlmodel import Field, SQLModel


class HubspotPersonMultipleCompanyHistories(SQLModel, table=True):
    __tablename__: str = "hubspot_person_multiple_company_histories"
    id: Optional[int] = Field(default=None, primary_key=True)
    hubspot_person_log_id: Optional[int] = Field(
        default=None, nullable=True, sa_column=Column(Integer)
    )
    matched_company_ids: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String(255)), nullable=True)
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
