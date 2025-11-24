from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, TIMESTAMP, Column, Integer, func
from sqlmodel import Field, SQLModel, Text


class SalesforcePersonMultiplePullHistories(SQLModel, table=True):
    __tablename__: str = "salesforce_person_multiple_pull_histories"
    id: Optional[int] = Field(default=None, primary_key=True)
    salesforce_person_history_id: Optional[int] = Field(
        default=None, nullable=True, sa_column=Column(Integer)
    )
    matched_company_ids: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(Text), nullable=True)
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
