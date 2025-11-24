from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, validator

from app.models.export_history import ExportStatus, ExportType


class ExportHistoryBase(BaseModel):
    id: int
    file_name: Optional[str] = None
    export_type: Optional[ExportType] = None
    status: Optional[ExportStatus] = None
    amount: Optional[int] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None

    @validator("file_name", check_fields=False)
    def format_file_name(cls, v):
        if not v:
            return None
        return v.split("/")[-1]


class ListExportHistoryResponse(BaseModel):
    data: List[ExportHistoryBase]
    total: int
    page: int
    per_page: int
