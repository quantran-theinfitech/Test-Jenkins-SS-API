from typing import Optional

from sqlalchemy import Column, Integer, String, Text
from sqlmodel import Field, Index, SQLModel


class Technology(SQLModel, table=True):
    __tablename__: str = "technologies"
    __table_args__ = (Index("idx_technology_corporate_number", "corporate_number"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    corporate_number: Optional[str] = Field(nullable=False, sa_column=Column(Text))
    name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
    website: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    icon: Optional[str] = Field(nullable=True, sa_column=Column(Text), default=None)
    technology_category_id: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
