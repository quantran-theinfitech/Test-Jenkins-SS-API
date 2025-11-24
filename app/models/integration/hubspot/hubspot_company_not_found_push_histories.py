from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, func
from sqlmodel import Field, SQLModel


class HubspotCompanyNotFoundPushHistories(SQLModel, table=True):
    __tablename__: str = "hubspot_company_not_found_push_histories"
    id: Optional[int] = Field(default=None, primary_key=True)
    hubspot_push_log_id: Optional[int] = Field(
        default=None, nullable=True, sa_column=Column(Integer)
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
