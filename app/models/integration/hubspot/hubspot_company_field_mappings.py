from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, String, func
from sqlmodel import Field, SQLModel


class HubspotCompanyFieldMappings(SQLModel, table=True):
    __tablename__: str = "hubspot_company_field_mappings"
    id: Optional[int] = Field(default=None, primary_key=True)
    integration_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    hubspot_team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    hubspot_field: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    field: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    field_class: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    overwrite_flag: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    autofill_flag: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    created_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    deleted_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
