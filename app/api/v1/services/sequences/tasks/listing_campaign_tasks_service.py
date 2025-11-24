# flake8: noqa: E501

from typing import Dict, List

from app.api.v1.services.media import media_service
from sqlalchemy import func
from sqlmodel import Session, asc, case, desc, select

from app.api.v1.schemas.sequence.tasks import ListingTaskRequest, TaskBase
from app.api.v1.schemas.sequence.tasks_person import TasksPerson
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.mail_histories.verify_campaign_permisstion_service import (
    verify_campaign_permission,
)
from app.models.sequence.contact import SequenceContact
from app.models.sequence.content_template import (
    ContentType,
    SequenceStepContentTemplate,
)
from app.models.sequence.mailbox import SequenceMailbox
from app.models.sequence.step import SequenceCampaignStep
from app.models.sequence.task import SequenceTask, TaskStatus, TaskType
from app.models.user import User


def get_campaign_tasks_statistics_service(
    campaign_id: int, db: Session, current_user: UserBase
) -> Dict:
    verify_campaign_permission(db, current_user, campaign_id)
    condition = [
        SequenceTask.sequence_campaign_id == campaign_id,
        SequenceTask.deleted_at.is_(None),
    ]
    statistics_query = select(
        func.count(SequenceTask.id).label("total"),
        func.count(
            case(
                (
                    SequenceTask.task_type == TaskType.EMAIL,
                    1,
                ),
                else_=None,
            )
        ).label("email_contact"),
    ).where(*condition)
    statistics = {
        "total": 0,
        "email_contact": 0,
    }
    statistics_result = db.exec(statistics_query).first()
    if statistics_result:
        total, email_contact = statistics_result
        statistics = {
            "total": total,
            "email_contact": email_contact,
        }
    return statistics


def listing_campaign_tasks_service(
    campaign_id: int, request: ListingTaskRequest, db: Session, current_user: UserBase
) -> List[TaskBase]:
    verify_campaign_permission(db, current_user, campaign_id)
    condition = [
        SequenceTask.sequence_campaign_id == campaign_id,
        SequenceTask.deleted_at.is_(None),
    ]

    if request.email:
        condition.append(SequenceContact.email.ilike(f"%{request.email}%"))
    if request.name:
        condition.append(SequenceContact.name.ilike(f"%{request.name}%"))
    if request.task_statuses:
        condition.append(SequenceTask.status.in_(request.task_statuses))
    else:
        condition.append(SequenceTask.status == TaskStatus.SCHEDULED)
    if request.step_ids:
        condition.append(SequenceTask.sequence_step_id.in_(request.step_ids))
    page = request.page
    per_page = request.per_page
    query = (
        select(SequenceTask, SequenceContact, SequenceStepContentTemplate, User)
        .join(SequenceContact, SequenceTask.sequence_person_id == SequenceContact.id)
        .join(User, SequenceTask.user_id == User.id, isouter=True)
        .join(
            SequenceCampaignStep,
            SequenceTask.sequence_step_id == SequenceCampaignStep.id,
            isouter=True,
        )
        .outerjoin(
            SequenceStepContentTemplate,
            SequenceCampaignStep.content_template_id == SequenceStepContentTemplate.id,
        )
        .where(*condition)
        .where(SequenceStepContentTemplate.content_type == ContentType.MAIL)
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    column = getattr(SequenceTask, request.order_by, None)
    if column:
        query = query.order_by(
            desc(column) if request.order_type == "desc" else asc(column)
        )

    mailbox = db.exec(
        select(SequenceMailbox)
        .where(
            SequenceMailbox.created_by == current_user.id,
            SequenceMailbox.deleted_at.is_(None),
        )
        .order_by(SequenceMailbox.id.asc())
    ).first()

    result = db.exec(query).all()
    response = []
    checkbox_status_default = False
    for task, person, mail_template, user in result:
        if mailbox:
            if mailbox.is_opt_out_message_after_signature:
                checkbox_status_default = True

            if (
                mailbox.is_opt_out_message_after_signature is False
                and mail_template.is_include_signature
            ):
                checkbox_status_default = True

        response.append(
            TasksPerson(
                **task.dict(),
                user_name=user.name,
                person_id=person.id,
                person_name=person.name,
                person_role_name=person.role_name,
                to_address=person.email,
                email_from=mailbox.email if mailbox else None,
                mailbox_id=mailbox.id if mailbox else None,
                is_reply_to_previous_thread=(
                    mail_template.is_reply_to_previous_thread
                    if mail_template
                    else False
                ),
                mail_template=mail_template.dict(),
                checkbox_status_default=checkbox_status_default,
                user_avatar= (
                    media_service.get_presigned_url(user.avatar_path) if user else None
                    ),
            )
        )
    return response


def count_campaign_tasks_service(
    campaign_id: int, db: Session, request: ListingTaskRequest, current_user: UserBase
):
    verify_campaign_permission(db, current_user, campaign_id)
    condition = [
        SequenceTask.sequence_campaign_id == campaign_id,
        SequenceTask.deleted_at.is_(None),
    ]
    if request.email:
        condition.append(SequenceContact.email.ilike(f"%{request.email}%"))
    if request.name:
        condition.append(SequenceContact.name.ilike(f"%{request.name}%"))
    if request.task_statuses:
        condition.append(SequenceTask.status.in_(request.task_statuses))
    else:
        condition.append(SequenceTask.status == TaskStatus.SCHEDULED)
    if request.step_ids:
        condition.append(SequenceTask.sequence_step_id.in_(request.step_ids))
    query = (
        select(func.count(SequenceTask.id))
        .join(SequenceContact, SequenceTask.sequence_person_id == SequenceContact.id)
        .where(*condition)
    )
    count = db.exec(query).one()
    return count
