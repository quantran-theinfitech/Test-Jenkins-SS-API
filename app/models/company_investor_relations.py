from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Integer, Text, func
from sqlmodel import Field, SQLModel


class CompanyInvestorRelations(SQLModel, table=True):
    __tablename__: str = "company_investor_relations"
    ir_id: str = Field(sa_column=Column(Text, primary_key=True))
    corporate_number: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    ir_company_name: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
    )
    ir_date: datetime = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=None)
    )
    ir_title: Optional[str] = Field(default=None, sa_column=Column(Text), nullable=True)
    ir_s3_url: Optional[str] = Field(
        default=None, sa_column=Column(Text), nullable=True
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
