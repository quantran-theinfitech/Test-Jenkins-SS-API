from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    TIMESTAMP,
    Column,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlmodel import Field, Index, SQLModel


class PressRelease(SQLModel, table=True):
    __tablename__: str = "press_releases"

    __table_args__ = (
        UniqueConstraint("media_code", "media_internal_id", name="articles_unique_id"),
        Index("idx_press_release_corporate_number", "corporate_number"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    media_internal_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    corporate_number: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    media_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    source_article_url: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    type_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    title: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    sub_title: Optional[str] = Field(
        nullable=True, sa_column=Column(Text), default=None
    )
    content: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    body_urls: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(2048))), default=None
    )
    business_category_texts: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    business_category_urls: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(2048))), default=None
    )
    prtimes_location_info_texts: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    prtimes_location_info_urls: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(2048))), default=None
    )
    keyword_texts: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(255))), default=None
    )
    keyword_urls: Optional[List[str]] = Field(
        nullable=True, sa_column=Column(ARRAY(String(2048))), default=None
    )
    posted_at_raw: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    posted_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    article_company_id: Optional[str] = Field(
        nullable=True, sa_column=Column(String(30)), default=None
    )
    created_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    created_by: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    updated_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_by: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    deleted_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    deleted_by: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
