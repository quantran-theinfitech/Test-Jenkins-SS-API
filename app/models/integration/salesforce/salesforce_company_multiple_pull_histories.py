from datetime import datetime
from typing import List, Optional

from sqlmodel import ARRAY, TIMESTAMP, Column, Field, Integer, SQLModel, String, func


class SalesforceCompanyMultiplePullHistories(SQLModel, table=True):
    __tablename__: str = "salesforce_company_multiple_pull_histories"
    id: Optional[int] = Field(default=None, primary_key=True)
    salesforce_pull_history_id: Optional[int] = Field(
        default=None, nullable=True, sa_column=Column(Integer)
    )
    matched_company_ids: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String(255)), nullable=True)
    )
    status: Optional[int] = Field(
        default=None, sa_column=Column(Integer, nullable=True)
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
