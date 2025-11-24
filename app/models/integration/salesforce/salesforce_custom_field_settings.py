from datetime import datetime
from typing import Optional

from sqlmodel import TIMESTAMP, Column, Field, Integer, SQLModel, String, func


class SalesforceCustomFieldSettings(SQLModel, table=True):
    __tablename__: str = "salesforce_custom_field_settings"
    id: Optional[int] = Field(default=None, primary_key=True)
    salesforce_integration_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    salesforce_team_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    field: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    display_name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    type: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    object_type: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
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
