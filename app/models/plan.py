import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, Column, Enum, Integer, String, func
from sqlmodel import Field, SQLModel


class PlanServiceCode(str, enum.Enum):
    LISTING = "LISTING"
    CPN = "CPN"
    PERSON = "PERSON"
    MSG = "MSG"
    FORM = "FORM"
    EMAIL = "EMAIL"
    CSV = "CSV"
    TELESALE = "TELESALE"
    LINKEDIN_CONNECT = "LINKEDIN_CONNECT"
    LINKEDIN_MSG = "LINKEDIN_MSG"


class Plan(SQLModel, table=True):
    __tablename__: str = "plans"
    id: Optional[int] = Field(default=None, primary_key=True)
    name_code: Optional[str] = Field(
        nullable=True, sa_column=Column(String(20)), default=None
    )
    service_code: Optional[PlanServiceCode] = Field(
        default=None, sa_column=Column(Enum(PlanServiceCode), nullable=True)
    )
    unlock_cpn_quota: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    send_form_quota: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    max_active_scenarios_number: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    unlock_person_quota: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    send_email_quota: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    download_csv_quota: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    telesale_quota: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    linkedin_connect_quota: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    linkedin_msg_quota: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
    )
    price: Optional[int] = Field(nullable=True, sa_column=Column(Integer), default=None)
    contract_month: Optional[int] = Field(
        nullable=True, sa_column=Column(Integer), default=None
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
