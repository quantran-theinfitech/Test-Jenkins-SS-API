from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, TIMESTAMP, Column, Integer, String, func
from sqlmodel import Field, SQLModel


class HubspotCompanyMultiplePushHistories(SQLModel, table=True):
    __tablename__: str = "hubspot_company_multiple_push_histories"
    id: Optional[int] = Field(default=None, primary_key=True)
    hubspot_push_log_id: Optional[int] = Field(
        default=None, nullable=True, sa_column=Column(Integer)
    )
    matched_company_ids: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String(255)), nullable=True)
    )
    status: Optional[int] = Field(
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
