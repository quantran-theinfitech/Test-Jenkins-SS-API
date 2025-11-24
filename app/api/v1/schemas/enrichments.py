from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Query
from pydantic import BaseModel
from sqlmodel import SQLModel

from app.models.enrichment import EnrichmentStatus, EnrichmentType
from app.models.enrichment_file import EnrichmentFileDelimiter, EnrichmentFileEncoding
from app.models.sequence.campaign_import import UploadProcessStatus


class EnrichmentBase(SQLModel):
    name: str
    type: EnrichmentType
    column_json_mapping: Dict = {}


class EnrichmentCreate(SQLModel):
    name: str
    type: EnrichmentType


class EnrichmentUpdate(SQLModel):
    name: Optional[str] = None


class EnrichmentFileBase(SQLModel):
    id: int
    enrichment_id: int
    file_name: str
    encoding: Optional[EnrichmentFileEncoding] = None
    delimiter: Optional[EnrichmentFileDelimiter] = None


class EnrichmentItemDataBase(SQLModel):
    id: int
    enrichment_item_id: int
    column_json_mapping_id: int
    value: str


class EnrichmentItemBase(SQLModel):
    id: int
    enrichment_id: int
    enrichment_file_id: Optional[int] = None
    entity_identifier: Optional[str] = None
    enrichment_item_data: Optional[List[EnrichmentItemDataBase]] = None


class TableEnrichmentResponse(SQLModel):
    page: int
    per_page: int
    total: int
    total_columns_uploaded: Optional[int] = None
    total_columns_mapped: Optional[int] = None
    identified_rows: int
    columns: List[Dict[str, str]]
    rows: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class EnrichmentVerifyFileResponse(SQLModel):
    is_compatible: bool
    total_rows: Optional[int] = None
    total_columns: Optional[int] = None


class EnrichmentUploadFileResponse(EnrichmentBase):
    id: int
    team_id: int
    total_rows: int
    total_columns: int

    class Config:
        from_attributes = True


class EnrichmentResponse(SQLModel):
    id: int
    team_id: int
    name: str
    type: Optional[EnrichmentType]
    status: Optional[EnrichmentStatus]
    process_status: Optional[UploadProcessStatus]
    table_enrichment_response: Optional[TableEnrichmentResponse]
    created_at: Optional[datetime]
    created_by: Optional[int]
    updated_at: Optional[datetime]
    updated_by: Optional[int]
    deleted_at: Optional[datetime]
    deleted_by: Optional[int]

    class Config:
        from_attributes = True


class EnrichmentListItemResponse(SQLModel):
    id: int
    team_id: int
    name: str
    enrichment_file: Optional[List[EnrichmentFileBase]]
    status: Optional[EnrichmentStatus]

    class Config:
        from_attributes = True


class EnrichmentListQueryParams(BaseModel):
    page: int = Query(default=1, ge=1)
    per_page: int = Query(default=10, ge=1)
    keyword: Optional[str] = Query(default=None)
    get_all: Optional[bool] = Query(default=False)


class EnrichmentListResponse(BaseModel):
    page: int
    per_page: int
    total: int
    data: List[EnrichmentListItemResponse]


class EnrichmentReIdentifyRequest(SQLModel):
    column_json_mapping: Optional[List[Dict]] = []


class GetTotalCompanyLockAndUnlockRequest(SQLModel):
    item_ids: List[int]


class GetTotalCompanyLockAndUnlockResponse(BaseModel):
    total: int
    total_identified: int
    total_lock: int
    total_unlock: int
    corporate_numbers: List[str]
