from fastapi import APIRouter, BackgroundTasks, Depends, Form, Query, UploadFile
from sqlmodel import Session

import app.api.v1.services.enrichments as enrichments_service
from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user, get_plan_code
from app.api.v1.schemas.enrichments import (
    EnrichmentCreate,
    EnrichmentFileDelimiter,
    EnrichmentFileEncoding,
    EnrichmentListQueryParams,
    EnrichmentListResponse,
    EnrichmentReIdentifyRequest,
    EnrichmentResponse,
    EnrichmentUpdate,
    EnrichmentUploadFileResponse,
    EnrichmentVerifyFileResponse,
    GetTotalCompanyLockAndUnlockRequest,
    GetTotalCompanyLockAndUnlockResponse,
)
from app.api.v1.schemas.users import UserBase
from app.models.enrichment import EnrichmentUploadFileMethod
from app.models.team import PlanCode
from utils.identify.identify_enrichment_service import identify_enrichment_file

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.post("/", response_model=EnrichmentResponse)
def create_enrichment(
    enrichment: EnrichmentCreate,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return enrichments_service.create_enrichment(
        db, enrichment, current_user.team_id, current_user.id
    )


@router.get("/{enrichment_id}", response_model=EnrichmentResponse)
def get_enrichment(
    enrichment_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return enrichments_service.get_enrichment(
        db,
        enrichment_id,
        current_user.team_id,
        listing_plan_code,
        page,
        per_page,
    )


@router.get("/", response_model=EnrichmentListResponse)
def list_enrichments(
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    query_params: EnrichmentListQueryParams = Depends(EnrichmentListQueryParams),
):
    data, total = enrichments_service.list_enrichments(
        db,
        current_user.team_id,
        query_params,
    )
    return EnrichmentListResponse(
        page=query_params.page,
        per_page=query_params.per_page,
        total=total,
        data=data,
    )


@router.patch("/{enrichment_id}", response_model=EnrichmentResponse)
def update_enrichment(
    enrichment_id: int,
    enrichment_update: EnrichmentUpdate,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return enrichments_service.update_enrichment(
        db,
        enrichment_id,
        enrichment_update,
        current_user.team_id,
        current_user.id,
        listing_plan_code,
    )


@router.delete("/{enrichment_id}", response_model=EnrichmentResponse)
def delete_enrichment(
    enrichment_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return enrichments_service.delete_enrichment(
        db,
        enrichment_id,
        current_user.team_id,
        current_user.id,
        listing_plan_code,
    )


@router.post("/{enrichment_id}/duplicate", response_model=EnrichmentResponse)
def duplicate_enrichment(
    enrichment_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return enrichments_service.duplicate_enrichment(
        db,
        enrichment_id,
        current_user.team_id,
        current_user.id,
        listing_plan_code,
    )


@router.post("/{enrichment_id}/identify")
def identify_enrichment(
    enrichment_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    enrichment = enrichments_service.update_enrichment_status(
        db, enrichment_id, current_user.team_id
    )
    background_tasks.add_task(
        identify_enrichment_file,
        db,
        enrichment,
        current_user.id,
    )


@router.post("/{enrichment_id}/re-identify")
def re_identify_enrichment(
    enrichment_id: int,
    enrichment_re_identify_request: EnrichmentReIdentifyRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    enrichments_service.update_column_json_mapping(
        db,
        enrichment_id,
        enrichment_re_identify_request.column_json_mapping,
        current_user.team_id,
        current_user.id,
    )

    enrichment = enrichments_service.update_enrichment_status(
        db, enrichment_id, current_user.team_id
    )

    background_tasks.add_task(
        identify_enrichment_file,
        db,
        enrichment,
        current_user.id,
    )


@router.post("/upload", response_model=EnrichmentUploadFileResponse)
async def upload_new_file_to_enrichment(
    file: UploadFile,
    column_json_mapping: str = Form(...),
    encoding: EnrichmentFileEncoding = Form(...),
    delimiter: EnrichmentFileDelimiter = Form(...),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    # background_tasks: BackgroundTasks = BackgroundTasks(),
):
    result = await enrichments_service.upload_enrichment_csv_file(
        db,
        file,
        current_user.team_id,
        current_user.id,
        encoding,
        delimiter,
        column_json_mapping,
    )
    enrichment = result["enrichment"]
    # background_tasks.add_task(
    #     identify_enrichment_file,
    #     db,
    #     enrichment,
    #     current_user.id,
    # )
    return EnrichmentUploadFileResponse(
        **enrichment.dict(),
        total_rows=result["total_rows"],
        total_columns=result["total_columns"],
    )


@router.post(
    "/{enrichment_id}/verify-upload", response_model=EnrichmentVerifyFileResponse
)
async def verify_enrichment_upload_file(
    enrichment_id: int,
    file: UploadFile,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return await enrichments_service.verify_enrichment_file(
        enrichment_id,
        file,
        db,
    )


@router.post("/{enrichment_id}/upload", response_model=EnrichmentUploadFileResponse)
async def upload_file_to_current_enrichment(
    enrichment_id: int,
    file: UploadFile,
    method: EnrichmentUploadFileMethod = Form(...),
    db: Session = Depends(get_session),
    encoding: EnrichmentFileEncoding = Form(...),
    delimiter: EnrichmentFileDelimiter = Form(...),
    current_user: UserBase = Depends(get_current_user()),
    # background_tasks: BackgroundTasks = BackgroundTasks(),
):
    result = await enrichments_service.upload_enrichment_csv_file(
        db,
        file,
        current_user.team_id,
        current_user.id,
        encoding,
        delimiter,
        enrichment_id=enrichment_id,
        method=method,
    )
    # enrichment = enrichments_service.update_enrichment_status(
    #     db, enrichment_id, current_user.team_id
    # )
    # background_tasks.add_task(
    #     identify_enrichment_file,
    #     db,
    #     enrichment,
    #     current_user.id,
    # )
    return EnrichmentUploadFileResponse(
        **result["enrichment"].dict(),
        total_rows=result["total_rows"],
        total_columns=result["total_columns"],
    )


@router.get("/{enrichment_id}/select_identified_items")
def select_identified_items(
    enrichment_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    current_page: bool = Query(default=True),
    page: int = Query(default=1),
    per_page: int = Query(default=10),
    total: int = Query(default=10000),
):
    return enrichments_service.select_identified_items(
        db, enrichment_id, current_user.team_id, current_page, page, per_page, total
    )


@router.post(
    "/{enrichment_id}/get-corporate-number-by-item-id",
    response_model=GetTotalCompanyLockAndUnlockResponse,
)
def get_corporate_number_by_item_id(
    enrichment_id: int,
    request: GetTotalCompanyLockAndUnlockRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return enrichments_service.get_corporate_number_by_item_id(
        db, enrichment_id, listing_plan_code, current_user, request.item_ids
    )
