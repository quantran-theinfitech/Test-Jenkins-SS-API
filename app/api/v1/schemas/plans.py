from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class PlanDetailResponse(BaseModel):
    name_code: Optional[str]
    unlock_cpn_quota: Optional[int]
    send_form_quota: Optional[int]
    max_active_scenarios_number: Optional[int]
    unlock_person_quota: Optional[int]
    send_email_quota: Optional[int]
    download_csv_quota: Optional[int]
    telesale_quota: Optional[int]
    price: Optional[int]
    contract_month: Optional[int]
    start_at: Optional[datetime]
    expire_at: Optional[datetime]
    linkedin_connect_quota: Optional[int]
    linkedin_message_quota: Optional[int]


class PlanHistory(BaseModel):
    name_code: Optional[str]
    unlock_cpn_quota: Optional[int]
    send_form_quota: Optional[int]
    max_active_scenarios_number: Optional[int]
    unlock_person_quota: Optional[int]
    send_email_quota: Optional[int]
    download_csv_quota: Optional[int]
    telesale_quota: Optional[int]
    price: Optional[int]
    contract_month: Optional[int]
    start_at: Optional[datetime]
    expire_at: Optional[datetime]
    is_active: Optional[bool]
    service_code: Optional[str]


class PlanHistoryResponse(BaseModel):
    page: int
    per_page: int
    total: int
    data: Optional[List[PlanHistory]]
