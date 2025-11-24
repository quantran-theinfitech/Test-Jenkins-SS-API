import enum
from datetime import datetime
from typing import Optional

from sqlmodel import (
    TIMESTAMP,
    Column,
    Enum,
    Field,
    Integer,
    SQLModel,
    String,
    Text,
    func,
)


class TYPE_INTEGRATION_ENUM(str, enum.Enum):
    SYNC_COMPANIES = "SYNC_COMPANIES"
    PULL_COMPANIES = "PULL_COMPANIES"
    PUSH_COMPANIES = "PUSH_COMPANIES"
    PULL_PERSONS = "PULL_PERSONS"


class METHOD_INTEGRATION_ENUM(str, enum.Enum):
    MANUAL = "MANUAL"
    AUTO = "AUTO"


class SalesforceSyncHistories(SQLModel, table=True):
    __tablename__: str = "salesforce_sync_histories"
    id: Optional[int] = Field(default=None, primary_key=True)
    salesforce_integration_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    salesforce_team_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    type: Optional[str] = Field(
        nullable=True,
        sa_column=Column(Enum(TYPE_INTEGRATION_ENUM)),
        default=TYPE_INTEGRATION_ENUM.PUSH_COMPANIES,
    )
    method: Optional[str] = Field(
        nullable=True,
        sa_column=Column(Enum(METHOD_INTEGRATION_ENUM)),
        default=METHOD_INTEGRATION_ENUM.AUTO,
    )
    log_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    total_companies: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    error_message: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    status: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    sync_count: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
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
