from datetime import datetime
from typing import Optional

from sqlmodel import TIMESTAMP, Column, Field, SQLModel, String, Text, func


class SalesforceManualPushCompanies(SQLModel, table=True):
    __tablename__: str = "salesforce_manual_push_companies"
    id: Optional[int] = Field(default=None, primary_key=True)
    ss_company_id: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
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
