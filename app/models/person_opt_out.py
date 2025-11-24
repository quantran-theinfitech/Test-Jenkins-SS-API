from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, String, UniqueConstraint, func
from sqlmodel import Field, SQLModel


class PersonOptOut(SQLModel, table=True):
    __tablename__: str = "person_opt_out"

    __table_args__ = (
        UniqueConstraint("person_uuid", name="person_opt_out_unique_uuid"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    person_uuid: Optional[str] = Field(
        nullable=True, sa_column=Column(String(64)), default=None
    )
    update_opt_out_at: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
