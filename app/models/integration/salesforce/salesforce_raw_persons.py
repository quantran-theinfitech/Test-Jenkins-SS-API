from datetime import datetime
from typing import Dict, Optional

from sqlmodel import (
    JSON,
    TIMESTAMP,
    Column,
    Field,
    Integer,
    SQLModel,
    String,
    Text,
    UniqueConstraint,
    func,
)


class SalesforceRawPersons(SQLModel, table=True):
    __tablename__: str = "salesforce_raw_persons"
    __table_args__ = (
        UniqueConstraint(
            "salesforce_team_id",
            "salesforce_integration_id",
            "salesforce_person_id",
            name="salesforce_raw_persons_unique_key",
        ),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    salesforce_team_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    salesforce_integration_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    salesforce_person_id: Optional[str] = Field(
        default=None, nullable=True, sa_column=Column(Text)
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
    deleted_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
