from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.v1.schemas.sequence.tasks import AddTaskRequest
from app.api.v1.schemas.users import UserBase
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_contacts import SequenceCampaignContacts
from app.models.sequence.contact import SequenceContact
from app.models.sequence.task import SequenceTask, TaskStatus


def create_campaign_task_service(
    campaign_id: int,
    request: AddTaskRequest,
    db: Session,
    current_user: UserBase,
):
    campaign = db.exec(
        select(SequenceCampaign).where(SequenceCampaign.id == campaign_id)
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="sequence.campaignNotFound")
    person = db.exec(
        select(SequenceContact)
        .join(
            SequenceCampaignContacts,
            SequenceContact.id == SequenceCampaignContacts.sequence_contact_id,
            isouter=False,
        )
        .where(
            SequenceContact.id == request.sequence_person_id,
            SequenceCampaignContacts.sequence_campaign_id == campaign_id,
            SequenceCampaignContacts.deleted_at.is_(None),
            SequenceCampaignContacts.status != "FINISH",
        )
    ).first()
    if not person:
        raise HTTPException(status_code=404, detail="sequence.personNotFound")
    task = SequenceTask(
        user_id=current_user.id,
        sequence_campaign_id=campaign_id,
        sequence_person_id=request.sequence_person_id,
        sequence_step_id=person.current_step,
        title=request.title,
        description=request.description,
        task_type=request.task_type,
        priority=request.priority,
        status=TaskStatus.SCHEDULED,
        due_date=request.due_date,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    campaign.updated_at = datetime.now()
    db.add(task)
    db.add(campaign)
    db.commit()
    # no need to refresh campaign; return task only
    db.refresh(task)

    return task
