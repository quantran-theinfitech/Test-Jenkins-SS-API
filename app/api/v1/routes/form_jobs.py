from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.api.v1.dependencies import (
    get_current_user,
    get_form_job_service,
    has_paid_plan,
)
from app.api.v1.schemas.form_jobs import (
    CreateFormJobRequest,
    CreateFormJobResponse,
    FormJobDetailResponse,
    FormJobItem,
    ListingFormJobItemsResponse,
    ListingFormJobsResponse,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.form_job_service import FormJobService
from app.models.team import PlanCode

router = APIRouter()


@router.post("", response_model=CreateFormJobResponse)
def create_form_job(
    request: CreateFormJobRequest,
    background_tasks: BackgroundTasks,
    plan_code: PlanCode = Depends(has_paid_plan),
    form_job_service: FormJobService = Depends(get_form_job_service),
    current_user: UserBase = Depends(get_current_user()),
):
    (
        total_company_collection_items,
        type_code,
    ) = form_job_service.count_company_collection_items(request, current_user)

    form_job_id, new_total_company_collection_items = form_job_service.create_form_job(
        total_company_collection_items, request, current_user, type_code
    )

    background_tasks.add_task(
        form_job_service.create_form_job_items,
        form_job_id,
        new_total_company_collection_items,
        request,
        current_user,
        type_code,
    )
    return CreateFormJobResponse(form_job_id=form_job_id)


@router.get("", response_model=ListingFormJobsResponse)
def listing_form_jobs(
    form_job_service: FormJobService = Depends(get_form_job_service),
    current_user: UserBase = Depends(get_current_user()),
    per_page: int = Query(default=10, ge=1),
    page: int = Query(default=1, ge=1),
    keyword: str = Query(default=""),
):
    data = form_job_service.listing_form_jobs(current_user, page, per_page, keyword)
    total = form_job_service.listing_form_jobs_count(current_user, keyword)
    return ListingFormJobsResponse(page=page, per_page=per_page, total=total, data=data)


@router.get("/{job_id}", response_model=ListingFormJobItemsResponse)
def listing_form_job_items(
    job_id: int,
    form_job_service: FormJobService = Depends(get_form_job_service),
    per_page: int = Query(default=10, ge=1),
    page: int = Query(default=1, ge=1),
    current_user: UserBase = Depends(get_current_user()),
):
    data = form_job_service.listing_form_job_items(
        job_id, page, per_page, current_user.team_id
    )
    total, contact_form_url_count = form_job_service.listing_form_job_items_count(
        job_id
    )

    not_send_contact_form_url_count = 0
    if total and contact_form_url_count:
        not_send_contact_form_url_count = total - contact_form_url_count

    if contact_form_url_count == 0:
        not_send_contact_form_url_count = total

    return ListingFormJobItemsResponse(
        page=page,
        per_page=per_page,
        job_id=job_id,
        total=total,
        contact_form_url_count=contact_form_url_count,
        not_send_contact_form_url_count=not_send_contact_form_url_count,
        data=[FormJobItem(**item) for item in data],
    )


@router.get("/{job_id}/detail", response_model=FormJobDetailResponse)
def get_form_job_detail(
    job_id: int,
    form_job_service: FormJobService = Depends(get_form_job_service),
    current_user: UserBase = Depends(get_current_user()),
):
    tags, description, job_name = form_job_service.get_tags_description(
        job_id, current_user
    )
    total, contact_form_url_count = form_job_service.listing_form_job_items_count(
        job_id
    )
    (
        id,
        template,
        placeholder,
        target_collection_id,
        exclude_collection_id,
        approach_ng_flag,
        schedule_at,
        max_resend_code,
        type_code,
        form_schedule_id,
    ) = form_job_service.get_form_job_detail(job_id, current_user)

    not_send_contact_form_url_count = 0
    if total and contact_form_url_count:
        not_send_contact_form_url_count = total - contact_form_url_count

    if contact_form_url_count == 0:
        not_send_contact_form_url_count = total

    return FormJobDetailResponse(
        id=id,
        template=template,
        placeholder=placeholder,
        target_collection_id=target_collection_id,
        exclude_collection_id=exclude_collection_id,
        approach_ng_flag=approach_ng_flag,
        schedule_at=schedule_at,
        max_resend_code=max_resend_code,
        tags=tags,
        description=description,
        job_name=job_name,
        total=total,
        type_code=type_code,
        form_schedule_id=form_schedule_id,
        not_send_contact_form_url_count=not_send_contact_form_url_count,
    )
