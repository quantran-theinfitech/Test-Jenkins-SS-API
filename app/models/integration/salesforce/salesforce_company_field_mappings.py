import enum
from datetime import datetime
from typing import Optional

from sqlmodel import (
    TIMESTAMP,
    Boolean,
    Column,
    Enum,
    Field,
    Integer,
    SQLModel,
    String,
    func,
)


class FIELD_CLASS_MAPPING_ENUM(str, enum.Enum):
    PREDEFINED = "PREDEFINED"
    CUSTOM = "CUSTOM"


class SalesforceCompanyFieldMappings(SQLModel, table=True):
    __tablename__: str = "salesforce_company_field_mappings"
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
    salesforce_field: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    field: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    field_class: Optional[str] = Field(
        nullable=True,
        sa_column=Column(Enum(FIELD_CLASS_MAPPING_ENUM)),
        default=FIELD_CLASS_MAPPING_ENUM.CUSTOM,
    )
    overwrite_flag: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    autofill_flag: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    created_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    deleted_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
