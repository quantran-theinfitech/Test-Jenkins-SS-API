from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    TIMESTAMP,
    Column,
    Float,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlmodel import Field, Index, SQLModel


class CompanyService(SQLModel, table=True):
    __tablename__: str = "company_services"

    __table_args__ = (
        UniqueConstraint(
            "media_code", "media_internal_id", name="company_services_unique_key"
        ),
        Index("idx_company_service_corporate_number", "corporate_number"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    ingest_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    corporate_number: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(64))), default=None
    )
    description: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    description_romaji: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    name: Optional[str] = Field(nullable=True, default=None)
    name_romaji: Optional[str] = Field(nullable=True, default=None)
    url: Optional[str] = Field(nullable=True, default=None)
    slug_tags: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    name_tags: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    media_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    media_internal_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(256)), default=None
    )
    title: Optional[str] = Field(default=None, sa_column=Column(Text), nullable=True)
    category: Optional[str] = Field(default=None, sa_column=Column(Text), nullable=True)
    sub_category: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    score: Optional[float] = Field(default=None, sa_column=Column(Float), nullable=True)
    created_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
