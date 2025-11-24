from typing import List, Optional

from app.api.base.exceptions import NotFoundException
from elasticsearch import Elasticsearch
from external.s3 import S3Service
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

import app.api.v1.services.investor_relations as investor_relations_service
from app.api.base.deps import custom_generate_unique_id, get_es, get_session
from app.api.v1.schemas.investor_relations import GetCompanyInvestorRelationsBase

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/", response_model=GetCompanyInvestorRelationsBase)
def listing_company_investor_relations(
    corporate_number: str,
    db: Session = Depends(get_session),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
):
    investor_relations = investor_relations_service.listing_company_investor_relations(
        db, corporate_number, per_page, page
    )
    total = investor_relations_service.listing_company_investor_relations_count(db, corporate_number)
    return GetCompanyInvestorRelationsBase(
        page=page, per_page=per_page, data=investor_relations, total=total
    )

@router.post("/download/{ir_id}")
def download_ir_file_route(
    ir_id: str,
    db: Session = Depends(get_session),
):
    file_path = investor_relations_service.download_ir_file(db, S3Service(), ir_id)
    if not file_path:
        raise NotFoundException(detail="common.notFound")
    return file_path
