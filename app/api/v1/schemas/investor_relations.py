from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.api.v1.schemas.search_recruits import MediaCode


class InvestorRelationsBase(BaseModel):
    ir_id: Optional[str] = None
    ir_title: Optional[str] = None
    ir_company_name: Optional[str] = None
    corporate_number: Optional[str] = None
    ir_s3_url: Optional[str] = None
    ir_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    created_by: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class GetCompanyInvestorRelationsBase(BaseModel):
    page: int
    per_page: int
    total: int
    data: List[InvestorRelationsBase]
