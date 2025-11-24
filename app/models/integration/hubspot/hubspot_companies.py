from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, TIMESTAMP, Column, Integer, String, func
from sqlmodel import Field, SQLModel


class HubspotCompanies(SQLModel, table=True):
    __tablename__: str = "hubspot_companies"
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
    predefined_fields: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
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
