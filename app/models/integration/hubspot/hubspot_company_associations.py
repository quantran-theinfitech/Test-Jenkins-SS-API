from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, String, func
from sqlmodel import Field, SQLModel


class HubspotCompanyAssociations(SQLModel, table=True):
    __tablename__: str = "hubspot_company_associations"
    id: Optional[int] = Field(default=None, primary_key=True)
    integration_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    hubspot_team_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    hubspot_company_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(50)), default=None
    )
    association_to: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    association_type_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    association_category: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
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
