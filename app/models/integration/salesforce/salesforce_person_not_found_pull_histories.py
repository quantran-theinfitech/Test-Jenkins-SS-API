from datetime import datetime
from typing import Optional

from sqlmodel import TIMESTAMP, Column, Field, Integer, SQLModel, func


class SalesforcePersonNotFoundPullHistories(SQLModel, table=True):
    __tablename__: str = "salesforce_person_not_found_pull_histories"
    id: Optional[int] = Field(default=None, primary_key=True)
    salesforce_person_history_id: Optional[int] = Field(
        default=None, nullable=True, sa_column=Column(Integer)
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
