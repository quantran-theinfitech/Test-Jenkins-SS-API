from datetime import datetime
from typing import Optional

from sqlmodel import TIMESTAMP, Column, Field, Index, SQLModel, String, Text, func


class SalesforcePersonPullHistories(SQLModel, table=True):
    __tablename__: str = "salesforce_person_pull_histories"
    __table_args__ = (Index("idx_salesforce_person_pull_histories_id", "id"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    salesforce_person_id: Optional[str] = Field(
        default=None, nullable=True, sa_column=Column(Text)
    )
    salesforce_company_id: Optional[str] = Field(
        default=None, nullable=True, sa_column=Column(Text)
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
