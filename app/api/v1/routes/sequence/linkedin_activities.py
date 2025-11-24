# flake8: noqa: E501
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies.authentication import get_current_user
from app.api.v1.schemas.sequence.linkedin_activities import (
    ChangeLinkedInAccountHistoryRequest,
    DeleteLinkedInActivityRequest,
    LinkedInActivityStatistics,
    LinkedInActivityStatus,
    LinkedInActivityType,
    ListingLinkedInActivityRequest,
    ListingLinkedInActivityResponse,
    RescheduleLinkedInActivityRequest,
    RetryLinkedInActivityRequest,
    SkipLinkedInActivityRequest,
    SortField,
    SortOrder,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.linkedin import (
    delete_linkedin_activity_service,
    get_linkedin_histories_statistics_service,
    list_linkedin_histories_service,
    reschedule_linkedin_activity_service,
    retry_linkedin_activity_service,
    skip_linkedin_activity_service,
)
from app.api.v1.services.sequences.linkedin.update_activity_executor_service import (
    update_activity_executor_service,
)
from app.api.v1.services.sequences.mail_histories.verify_campaign_permisstion_service import (
    verify_campaign_permission,
)

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get(
    "/{sequence_campaign_id}/linkedin/activities",
    response_model=ListingLinkedInActivityResponse,
)
def list_linkedin_activities(
    sequence_campaign_id: int,
    page: int = Query(default=1),
    per_page: int = Query(default=5),
    sort: SortField = Query(default=SortField.SENT_DATE),
    order: SortOrder = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    types: List[LinkedInActivityType] = Query(
        default=[
            "LINKEDIN_AUTO_MESSAGE",
            "LINKEDIN_CONNECTION_REQUEST",
            "LINKEDIN_VIEW_PROFILE",
        ]
    ),
    statuses: Optional[List[LinkedInActivityStatus]] = Query(default=None),
    step_ids: Optional[List[int]] = Query(default=None),
    linkedin_user_id: Optional[int] = Query(default=None),
    linkedin_senders: Optional[List[str]] = Query(default=None),
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    request = ListingLinkedInActivityRequest(
        page=page,
        per_page=per_page,
        sort=sort,
        order=order,
        keyword=keyword,
        types=types,
        statuses=statuses,
        step_ids=step_ids,
        linkedin_user_id=linkedin_user_id,
        linkedin_senders=linkedin_senders,
    )
    verify_campaign_permission(db, current_user, sequence_campaign_id)
    response, total = list_linkedin_histories_service(
        db=db,
        sequence_campaign_id=sequence_campaign_id,
        current_user=current_user,
        request=request,
    )
    return ListingLinkedInActivityResponse(
        page=page, per_page=per_page, total=total, data=response
    )


@router.get(
    "/{sequence_campaign_id}/linkedin/activities/statistics",
    response_model=LinkedInActivityStatistics,
)
def get_linkedin_activities_statistics(
    sequence_campaign_id: int,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    verify_campaign_permission(db, current_user, sequence_campaign_id)
    return get_linkedin_histories_statistics_service(
        db, sequence_campaign_id, current_user, None
    )


@router.put("/linkedin_activities/reschedule")
def reschedule_linkedin_activity(
    request: RescheduleLinkedInActivityRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    if not reschedule_linkedin_activity_service(db, request, current_user):
        return JSONResponse(status_code=200, content={"success": True})
    else:
        raise HTTPException(status_code=400, detail="sequence.allActivitiesFinished")


@router.put("/linkedin_activities/retry")
def retry_linkedin_activity(
    request: RetryLinkedInActivityRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    if not retry_linkedin_activity_service(db, request, current_user):
        return JSONResponse(status_code=200, content={"success": True})
    else:
        raise HTTPException(status_code=400, detail="sequence.allActivitiesFinished")


@router.put("/linkedin_activities/skip")
def skip_linkedin_activity(
    request: SkipLinkedInActivityRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    if not skip_linkedin_activity_service(db, request, current_user):
        return JSONResponse(status_code=200, content={"success": True})
    else:
        raise HTTPException(status_code=400, detail="sequence.allActivitiesFinished")


@router.put("/linkedin_activities/delete")
def delete_linkedin_activity(
    request: DeleteLinkedInActivityRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    success = delete_linkedin_activity_service(db, request, current_user)
    return {"success": success}


@router.put("/linkedin_activities/executor")
def update_activities_executor(
    request: ChangeLinkedInAccountHistoryRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    if not update_activity_executor_service(db, request, current_user):
        return JSONResponse(status_code=200, content={"success": True})
    else:
        raise HTTPException(status_code=400, detail="sequence.allActivitiesFinished")
