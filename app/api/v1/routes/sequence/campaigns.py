from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user
from app.api.v1.dependencies.credit import get_plan_code
from app.api.v1.schemas.sequence.campaign_settings import (
    SequenceCampaignSettingBase,
    SequenceCampaignSettingResponse,
    UpdateCampaignSettingRequest,
)
from app.api.v1.schemas.sequence.campaigns import (
    AddStepRequest,
    CreateCampaignRequest,
    DeleteCampaignRequest,
    ListingCampaignRequest,
    ListingImportContactsRequest,
    ListingSequenceImportContactsResponse,
    ListingSequenceOwnerResponse,
    ListingSequenceResponse,
    PersonStages,
    ReorderCampaignStepsRequest,
    SequenceBase,
    StepBase,
    StepList,
    UpdateCampaignPersonsRequest,
    UpdateCampaignRequest,
    UpdateCampaignResponse,
    UpdateStepRequest,
)
from app.api.v1.schemas.sequence.tasks import (
    AddTaskRequest,
    ListingTaskRequest,
    SortField,
    SortOrder,
    TaskBase,
    TaskStatus,
    TriggerTaskRequest,
    UpdateTaskRequest,
)
from app.api.v1.schemas.sequence.tasks_person import TaskList, TaskStatistics
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.campaigns import (
    create_campaign_service,
    create_campaign_step_service,
    delete_campaign_service,
    delete_step_service,
    get_active_campaign_warning_service,
    get_campaign_service,
    get_campaign_setting_service,
    get_detail_step_service,
    get_listing_step_service,
    get_person_stages_service,
    get_sequence_owner,
    list_campaign_add_contacts_service,
    list_campaign_service,
    reorder_sequence_campaign_steps,
    update_campaign_persons_service,
    update_campaign_service,
    update_campaign_setting_service,
    update_campaign_step_service,
)
from app.api.v1.services.sequences.tasks import (
    count_campaign_tasks_service,
    create_campaign_task_service,
    delete_campaign_task_service,
    get_campaign_tasks_statistics_service,
    listing_campaign_tasks_service,
    trigger_task_service,
    update_campaign_task_service,
)
from app.models.team import PlanCode
from external.mautic.event_service import trigger_event_service
from external.mautic.schema.campaign import MauticTriggerEventRequest

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get(
    "/campaigns/sequence_owner", response_model=List[ListingSequenceOwnerResponse]
)
def get_shared_sequence_owner(
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return get_sequence_owner(db, current_user)


@router.get("/campaigns", response_model=ListingSequenceResponse)
def get_list_sequence_campaigns(
    params: ListingCampaignRequest = Depends(),
    owner_id: Optional[List[int]] = Query(default=None),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    campaign, total = list_campaign_service(db, current_user, params, owner_id)
    return ListingSequenceResponse(
        data=campaign, total=total, page=params.page, per_page=params.per_page
    )


@router.get(
    "/campaigns-add-contacts", response_model=ListingSequenceImportContactsResponse
)
def get_list_campaign_add_contacts(
    params: ListingImportContactsRequest = Depends(),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    contacts, total = list_campaign_add_contacts_service(db, current_user, params)
    return ListingSequenceImportContactsResponse(
        data=contacts, total=total, page=params.page, per_page=params.per_page
    )


@router.post("/campaigns", response_model=SequenceBase)
def create_sequence_campaign(
    request: CreateCampaignRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return create_campaign_service(db, request, current_user)


@router.get("/steps/{step_id}", response_model=StepBase)
def get_sequence_campaign_step(
    step_id: int,
    db: Session = Depends(get_session),
):
    step = get_detail_step_service(db, step_id)
    return step


@router.put("/steps/{step_id}")
def update_sequence_campaign_step(
    step_id: int,
    request: UpdateStepRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return update_campaign_step_service(db, current_user, step_id, request)


@router.delete("/steps/{step_id}")
def delete_sequence_campaign_step(
    step_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    success = delete_step_service(db, current_user, step_id)
    return {"success": success}


@router.post("/campaigns/{campaign_id}/steps", response_model=StepBase)
def create_sequence_campaign_step(
    campaign_id: int,
    request: AddStepRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    step = create_campaign_step_service(db, current_user, campaign_id, request)
    return step


@router.get("/campaigns/{campaign_id}/steps", response_model=StepList)
def get_listing_step(
    campaign_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    step_list = get_listing_step_service(campaign_id, db, current_user)
    return StepList(data=step_list)


@router.get(
    "/active_campaign_warning/{campaign_id}", response_model=UpdateCampaignResponse
)
def get_active_campaign_warning(
    campaign_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    data = get_active_campaign_warning_service(db, current_user, campaign_id)
    return data


@router.get("/campaigns/{campaign_id}", response_model=SequenceBase)
def get_sequence_campaign(
    campaign_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    data = get_campaign_service(db, current_user, campaign_id)
    return data


@router.delete("/campaigns")
def delete_sequence_campaign(
    request: DeleteCampaignRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    success = delete_campaign_service(db, current_user, request.campaign_ids)
    return {"success": success}


@router.put("/campaigns/{campaign_id}")
def update_sequence_campaign(
    campaign_id: int,
    request: UpdateCampaignRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    return update_campaign_service(
        db, current_user, campaign_id, request, listing_plan_code
    )


@router.get("/campaigns/{campaign_id}/person_stages", response_model=PersonStages)
def get_person_stages(
    campaign_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    data = get_person_stages_service(db, current_user, campaign_id)
    return data


@router.put("/campaigns/{campaign_id}/status")
def update_campaign_persons_status(
    campaign_id: int,
    request: UpdateCampaignPersonsRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    if not update_campaign_persons_service(db, current_user, campaign_id, request):
        return JSONResponse(
            status_code=200,
            content={"success": True},
        )
    else:
        raise HTTPException(status_code=400, detail="sequence.allContactsFinished")


@router.post("/trigger")
def mautic_trigger_event(
    background_tasks: BackgroundTasks,
    request: MauticTriggerEventRequest,
    db: Session = Depends(get_session),
):
    print(f"Mautic trigger event {request}")
    background_tasks.add_task(trigger_event_service, request, db)


@router.post("/tasks/trigger")
def trigger_campaign_task(
    request: TriggerTaskRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    if not trigger_task_service(db, request, current_user):
        return JSONResponse(status_code=200, content={"success": True})
    else:
        raise HTTPException(status_code=400, detail="sequence.allTasksFinished")


@router.post("/campaigns/{campaign_id}/tasks", status_code=201, response_model=TaskBase)
def create_campaign_task(
    campaign_id: int,
    request: AddTaskRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return create_campaign_task_service(campaign_id, request, db, current_user)


@router.get("/campaigns/{campaign_id}/tasks", response_model=TaskList)
def get_campaign_tasks(
    campaign_id: int,
    page: Optional[int] = Query(default=1),
    per_page: Optional[int] = Query(default=5),
    email: Optional[str] = Query(default=None),
    name: Optional[str] = Query(default=None),
    order_by: Optional[SortField] = SortField.DUE_DATE,
    order_type: Optional[SortOrder] = SortOrder.ASC,
    task_statuses: Optional[List[TaskStatus]] = Query(default=None),
    step_ids: Optional[List[int]] = Query(default=None),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    request = ListingTaskRequest(
        page=page,
        per_page=per_page,
        email=email,
        name=name,
        order_by=order_by,
        order_type=order_type,
        task_statuses=task_statuses,
        step_ids=step_ids,
    )
    tasks = listing_campaign_tasks_service(campaign_id, request, db, current_user)
    total = count_campaign_tasks_service(campaign_id, db, request, current_user)
    return TaskList(
        data=tasks,
        total=total,
        page=request.page,
        per_page=request.per_page,
    )


@router.get("/campaigns/{campaign_id}/tasks/statistics", response_model=TaskStatistics)
def get_campaign_tasks_statistics(
    campaign_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return get_campaign_tasks_statistics_service(campaign_id, db, current_user)


@router.put("/campaigns/{campaign_id}/tasks")
def update_campaign_task(
    campaign_id: int,
    request: UpdateTaskRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    if not update_campaign_task_service(campaign_id, request, db, current_user):
        return JSONResponse(status_code=200, content={"success": True})
    else:
        raise HTTPException(status_code=400, detail="sequence.allTasksFinished")


@router.delete("/campaigns/{campaign_id}/tasks", status_code=204)
def delete_campaign_task(
    campaign_id: int,
    task_id: List[int] = Query(None),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    delete_campaign_task_service(campaign_id, task_id, db, current_user)


@router.post("/steps/reorder", status_code=204)
def reorder_campaign_steps(
    request: ReorderCampaignStepsRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    reorder_sequence_campaign_steps(db, current_user, request)


@router.get(
    "/campaigns/{campaign_id}/setting", response_model=SequenceCampaignSettingResponse
)
def get_campaign_setting(
    campaign_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return get_campaign_setting_service(campaign_id, db, current_user)


@router.put(
    "/campaigns/{campaign_id}/setting", response_model=SequenceCampaignSettingBase
)
def update_campaign_setting(
    campaign_id: int,
    request: UpdateCampaignSettingRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return update_campaign_setting_service(campaign_id, request, db, current_user)
