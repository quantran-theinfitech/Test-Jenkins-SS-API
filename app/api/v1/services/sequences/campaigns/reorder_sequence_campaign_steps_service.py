from datetime import datetime

from sqlmodel import Session, delete, select, update

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.sequence.campaigns import ReorderCampaignStepsRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.campaigns.get_sequence_campaign_step_service import (
    get_total_days_count,
)
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.contact import SequenceContact
from app.models.sequence.mail_history import MailHistoryStatus, SequenceMailHistory
from app.models.sequence.step import SequenceCampaignStep, StepType
from app.models.sequence.task import SequenceTask, TaskStatus, TaskType
from celery_worker.send_mail_service import get_due_date


def reorder_sequence_campaign_steps(
    db: Session, current_user: UserBase, request: ReorderCampaignStepsRequest
):
    try:
        reordered_step = db.exec(
            select(SequenceCampaignStep).where(
                SequenceCampaignStep.id == request.step_id
            )
        ).one_or_none()
        if not reordered_step:
            raise NotFoundException("Step not found")

        campaign = db.exec(
            select(SequenceCampaign).where(
                SequenceCampaign.id == reordered_step.sequence_campaign_id,
                SequenceCampaign.deleted_at.is_(None),
                SequenceCampaign.team_id == current_user.team_id,
            )
        ).first()
        if not campaign:
            raise NotFoundException("Campaign not found")
        campaign.updated_at = datetime.now()
        db.add(campaign)

        if request.previous_step_id:
            previous_step = db.exec(
                select(SequenceCampaignStep).where(
                    SequenceCampaignStep.id == request.previous_step_id,
                    SequenceCampaignStep.sequence_campaign_id
                    == reordered_step.sequence_campaign_id,
                )
            ).one_or_none()
            if not previous_step:
                raise NotFoundException("Step not found")

            if reordered_step.order < previous_step.order:
                new_order = previous_step.order
                db.exec(
                    update(SequenceCampaignStep)
                    .where(
                        SequenceCampaignStep.sequence_campaign_id
                        == reordered_step.sequence_campaign_id
                    )
                    .where(SequenceCampaignStep.order > reordered_step.order)
                    .where(SequenceCampaignStep.order <= previous_step.order)
                    .values(order=SequenceCampaignStep.order - 1)
                )
            else:
                new_order = previous_step.order + 1
                db.exec(
                    update(SequenceCampaignStep)
                    .where(
                        SequenceCampaignStep.sequence_campaign_id
                        == reordered_step.sequence_campaign_id
                    )
                    .where(SequenceCampaignStep.order < reordered_step.order)
                    .where(SequenceCampaignStep.order > previous_step.order)
                    .values(order=SequenceCampaignStep.order + 1)
                )
        else:
            new_order = 1
            db.exec(
                update(SequenceCampaignStep)
                .where(
                    SequenceCampaignStep.sequence_campaign_id
                    == reordered_step.sequence_campaign_id
                )
                .where(SequenceCampaignStep.order < reordered_step.order)
                .values(order=SequenceCampaignStep.order + 1)
            )

        reordered_step.order = new_order
        db.add(reordered_step)
        db.flush()
        # Recalculate total_days for all steps after reorder
        steps_after_reorder = db.exec(
            select(SequenceCampaignStep)
            .where(
                SequenceCampaignStep.sequence_campaign_id
                == reordered_step.sequence_campaign_id,
                SequenceCampaignStep.deleted_at.is_(None),
            )
            .order_by(SequenceCampaignStep.order.asc())
        ).all()
        if steps_after_reorder:
            for index, s in enumerate(steps_after_reorder, start=1):
                s.total_days = get_total_days_count(steps_after_reorder[:index])
                db.add(s)
        _reorder_mail_history_next_step(db, campaign)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e


def _reorder_mail_history_next_step(
    db: Session,
    campaign: SequenceCampaign,
):
    persons = db.exec(
        select(SequenceContact)
        .join(
            SequenceCampaignContacts,
            SequenceContact.id == SequenceCampaignContacts.sequence_contact_id,
        )
        .where(
            SequenceCampaignContacts.sequence_campaign_id == campaign.id,
            SequenceCampaignContacts.status != StatusEnum.FINISH,
            SequenceCampaignContacts.deleted_at.is_(None),
            SequenceContact.deleted_at.is_(None),
        )
    ).all()

    step_mapping = dict()

    steps = db.exec(
        select(SequenceCampaignStep).where(
            SequenceCampaignStep.sequence_campaign_id == campaign.id,
            SequenceCampaignStep.deleted_at.is_(None),
        )
    ).all()

    for step in steps:
        step_mapping[step.order] = step

    for person in persons:
        done_step = db.exec(
            select(SequenceMailHistory).where(
                SequenceMailHistory.sequence_contact_id == person.id,
                SequenceMailHistory.sequence_campaign_id == campaign.id,
                SequenceMailHistory.status != MailHistoryStatus.SCHEDULED,
                SequenceMailHistory.deleted_at.is_(None),
            )
        ).all()
        done_step_ids = [d.sequence_step_id for d in done_step]
        if not step_mapping.get(person.current_step):
            continue

        while True:
            new_step = step_mapping.get(person.current_step)
            if not new_step or new_step.id not in done_step_ids:
                break
            if person.current_step + 1 not in step_mapping:
                new_step = None
                break
            person.current_step += 1

        if not new_step:
            db.exec(
                update(SequenceCampaignContacts)
                .where(
                    SequenceCampaignContacts.sequence_contact_id == person.id,
                    SequenceCampaignContacts.sequence_campaign_id == campaign.id,
                )
                .values(status=StatusEnum.FINISH, updated_at=datetime.now())
            )
            db.exec(
                delete(SequenceMailHistory).where(
                    SequenceMailHistory.sequence_contact_id == person.id,
                    SequenceMailHistory.sequence_campaign_id == campaign.id,
                    SequenceMailHistory.status == MailHistoryStatus.SCHEDULED,
                    SequenceMailHistory.deleted_at.is_(None),
                )
            )
            continue

        person.current_step = new_step.order
        last_person_mail_history = db.exec(
            select(SequenceMailHistory)
            .where(
                SequenceMailHistory.sequence_contact_id == person.id,
                SequenceMailHistory.sequence_campaign_id == campaign.id,
                SequenceMailHistory.status != MailHistoryStatus.SCHEDULED,
                SequenceMailHistory.deleted_at.is_(None),
            )
            .order_by(SequenceMailHistory.sent_at.desc())
        ).first()

        if (
            last_person_mail_history
            and new_step.id != last_person_mail_history.next_sequence_step_id
        ):
            last_person_mail_history.next_sequence_step_id = new_step.id

        # manual
        # delete current schedule mail
        # db.exec(
        #     update(SequenceMailHistory)
        #     .where(
        #         SequenceMailHistory.sequence_contact_id == person.id,
        #         SequenceMailHistory.sequence_campaign_id == campaign.id,
        #         SequenceMailHistory.status == MailHistoryStatus.SCHEDULED,
        #         SequenceMailHistory.deleted_at.is_(None),
        #     )
        #     .values(deleted_at=datetime.now())
        # )
        db.exec(
            delete(SequenceMailHistory).where(
                SequenceMailHistory.sequence_contact_id == person.id,
                SequenceMailHistory.sequence_campaign_id == campaign.id,
                SequenceMailHistory.status == MailHistoryStatus.SCHEDULED,
            )
        )

        # delete current schedule task
        db.exec(
            update(SequenceTask)
            .where(
                SequenceTask.sequence_person_id == person.id,
                SequenceTask.sequence_campaign_id == campaign.id,
                SequenceTask.status == TaskStatus.SCHEDULED,
                SequenceTask.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now())
        )

        if new_step.step_type == StepType.MAIL_MANUAL:
            task = SequenceTask(
                team_id=campaign.team_id,
                user_id=campaign.created_by,
                sequence_campaign_id=campaign.id,
                sequence_step_id=new_step.id,
                task_type=TaskType.EMAIL,
                sequence_person_id=person.id,
                due_date=get_due_date(new_step),
                priority=new_step.priority,
                status=TaskStatus.SCHEDULED,
                created_at=datetime.now(),
                created_by=campaign.created_by,
            )
            db.add(task)

    db.commit()
