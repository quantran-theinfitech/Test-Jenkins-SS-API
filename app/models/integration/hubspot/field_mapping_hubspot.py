from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Boolean, Column, String, func
from sqlmodel import Field, SQLModel


class FieldMappingHubspot(SQLModel, table=True):
    __tablename__: str = "field_mapping_hubspot"
    id: Optional[int] = Field(default=None, primary_key=True)
    sale_smart_field: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    hubspot_field: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    is_over_write: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    is_auto_fill: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    is_suggested_field: Optional[bool] = Field(default=False, sa_column=Column(Boolean))
    created_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    deleted_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
