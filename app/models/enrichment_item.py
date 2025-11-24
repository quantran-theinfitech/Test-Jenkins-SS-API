from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Enum, Integer, String
from sqlmodel import Field, SQLModel, func

from app.models.enrichment import EnrichmentStatus


class EnrichmentItem(SQLModel, table=True):
    __tablename__: str = "enrichment_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    enrichment_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    enrichment_file_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    entity_identifier: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    status: Optional[EnrichmentStatus] = Field(
        sa_column=Column(
            Enum(EnrichmentStatus, name="enrichment_item_status"),
            default=None,
        )
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
