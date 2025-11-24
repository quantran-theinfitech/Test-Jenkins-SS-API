from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.sequence.tasks import UpdateTaskRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.mail_histories.handle_schedule_time import (
    handle_schedule_time,
)
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.task import SequenceTask, TaskStatus


def update_campaign_task_service(
    campaign_id: int,
    request: UpdateTaskRequest,
    db: Session,
    current_user: UserBase,
):
    all_finished = True
    # update sequence.updated_at
    campaign = db.exec(
        select(SequenceCampaign).where(
            SequenceCampaign.id == campaign_id, SequenceCampaign.deleted_at.is_(None)
        )
    ).first()
    if not campaign:
        raise NotFoundException("SequenceCampaign not found")
    campaign.updated_at = datetime.now()
    db.add(campaign)

    condition = [
        SequenceTask.sequence_campaign_id == campaign_id,
        SequenceTask.id.in_(request.task_ids),
        SequenceTask.deleted_at.is_(None),
    ]
    query = select(SequenceTask).where(*condition)
    tasks = db.exec(query).all()
    if not tasks:
        raise HTTPException(status_code=404, detail="sequence.taskNotFound")
    request_dict = request.dict(
        exclude_unset=True, exclude={"task_ids", "schedule_type", "custom_datetime"}
    )
    for task in tasks:
        if task.status in [TaskStatus.ARCHIVED, TaskStatus.COMPLTETED]:
            continue  # SKIP LOGIC IF ARCHIVED OR COMPLETED
        for key, value in request_dict.items():
            setattr(task, key, value)
        schedule_time = handle_schedule_time(
            request.schedule_type, request.custom_datetime
        )
        task.due_date = schedule_time
        task.updated_at = datetime.now()
        task.updated_by = current_user.id
        db.add(task)
        all_finished = False

    db.commit()
    for task in tasks:
        db.refresh(task)
    return all_finished
