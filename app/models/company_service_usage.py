from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, String, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


class CompanyServiceUsage(SQLModel, table=True):
    __tablename__ = "company_service_usage"
    __table_args__ = (
        UniqueConstraint(
            "corporate_number",
            "article_id",
            "service_id",
            name="company_service_usage_unique",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    corporate_number: Optional[str] = Field(
        default=None, sa_column=Column(String(20), nullable=True, server_default=None)
    )
    article_id: Optional[str] = Field(
        sa_column=Column(Text, nullable=False, server_default=None)
    )
    service_id: Optional[str] = Field(
        sa_column=Column(Text, nullable=False, server_default=None)
    )
    posted_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, nullable=True, server_default=None)
    )
    service_name: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True, server_default=None)
    )
    service_url: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True, server_default=None)
    )
    article_url: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True, server_default=None)
    )
