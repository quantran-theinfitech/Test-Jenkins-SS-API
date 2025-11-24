from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, Text
from sqlmodel import Field, SQLModel, func


class EnrichmentItemData(SQLModel, table=True):
    __tablename__: str = "enrichment_item_data"

    id: Optional[int] = Field(default=None, primary_key=True)
    enrichment_item_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    column_json_mapping_id: int = Field(sa_column=Column(Integer))
    value: str = Field(sa_column=Column(Text()))
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
