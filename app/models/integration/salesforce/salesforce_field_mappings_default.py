import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Boolean, Column, String, func
from sqlmodel import Enum, Field, SQLModel

from app.models.integration.salesforce.salesforce_company_field_mappings import (
    FIELD_CLASS_MAPPING_ENUM,
)


class OBJECT_TYPE_ENUM(str, enum.Enum):
    PERSONS = "PERSONS"
    COMPANIES = "COMPANIES"


class SalesforceFieldMappingDefault(SQLModel, table=True):
    __tablename__: str = "salesforce_field_mappings_default"
    id: Optional[int] = Field(default=None, primary_key=True)
    salesmart_field: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    salesforce_field: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    is_over_write: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    is_auto_fill: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    is_suggested_field: Optional[bool] = Field(default=False, sa_column=Column(Boolean))
    field_class: Optional[str] = Field(
        nullable=True,
        sa_column=Column(Enum(FIELD_CLASS_MAPPING_ENUM)),
        default=FIELD_CLASS_MAPPING_ENUM.PREDEFINED,
    )
    object_type: Optional[str] = Field(
        nullable=True,
        sa_column=Column(Enum(OBJECT_TYPE_ENUM)),
        default=OBJECT_TYPE_ENUM.COMPANIES,
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
