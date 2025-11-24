from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, String, func
from sqlmodel import Field, SQLModel


class PressReleaseBusinessCategory(SQLModel, table=True):
    __tablename__: str = "press_release_business_categories"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(255)), default=None
    )
    created_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
