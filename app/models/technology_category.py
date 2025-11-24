from typing import Optional

from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel


class TechnologyCategory(SQLModel, table=True):
    __tablename__: str = "technology_categories"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(
        nullable=True, sa_column=Column(String(1024)), default=None
    )
