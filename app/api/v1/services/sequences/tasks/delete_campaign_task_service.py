from datetime import datetime
from typing import List

from fastapi import HTTPException
from sqlmodel import Session, select
from app.api.base.exceptions import BadRequestException, NotFoundException
from app.api.v1.schemas.users import UserBase
from app.models.sequence.task import SequenceTask
from app.models.sequence.campaign import SequenceCampaign

def delete_campaign_task_service(
    campaign_id: int,
    task_id: List[int],
    db: Session,
    current_user: UserBase,
):
    #update sequence.updated_at when deleting task
    campaign = db.exec(
        select(SequenceCampaign).where(
            SequenceCampaign.id == campaign_id,
            SequenceCampaign.deleted_at.is_(None)
        )
    ).first()
    if not campaign:
        raise NotFoundException('SequenceCampaign not found')
    campaign.updated_at = datetime.now()
    db.add(campaign)
    
    condition = [
        SequenceTask.sequence_campaign_id == campaign_id,
        SequenceTask.id.in_(task_id),
        SequenceTask.deleted_at.is_(None),
    ]
    query = select(SequenceTask).where(*condition)
    tasks = db.exec(query).all()
    if not tasks:
        raise HTTPException(status_code=404, detail="sequence.taskNotFound")
    for task in tasks:
        task.deleted_at = datetime.now()
        task.deleted_by = current_user.id
        db.add(task)
    
    db.commit()
