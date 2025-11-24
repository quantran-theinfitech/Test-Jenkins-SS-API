# flake8: noqa: E501
from collections import defaultdict
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, Query
from sqlmodel import Session, asc, case, desc, func, or_, select, text, update

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.sequence.campaigns import (
    ListingCampaignRequest,
    ListingImportContactsRequest,
    ListingSequenceOwnerResponse,
    SequenceCampaignOrderEnum,
    SequenceCampaignOrderTypeEnum,
    SequenceCampaignStatusEnum,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.media import media_service
from app.api.v1.services.sequences.linkedin.get_list_linkedin_activities_service import (
    get_linkedin_histories_statistics_service,
)
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.contact import SequenceContact
from app.models.sequence.content_items import ContentItemsType, SequenceStepContentItem
from app.models.sequence.content_template import (
    ContentType,
    SequenceStepContentTemplate,
)
from app.models.sequence.mail_history import (
    MAIL_HISTORY_VIEW_NAME,
    MailHistoryBounceSubType,
    MailHistoryStatus,
    SequenceMailHistory,
)
from app.models.sequence.step import SequenceCampaignStep, StepType
from app.models.sequence.task import SequenceTask, TaskStatus, TaskType
from app.models.team_credit import ServiceCode
from app.models.user import User
from celery_worker.send_mail_service import get_due_date
from utils.credit_utils import is_enough_credit
from utils.sequence_schedule import validate_campaign_on_sending_window


def get_email_stat(sequence_campaign_id, sequence_step_id, db):
    spam_subtype = [
        MailHistoryBounceSubType.SUPPRESSED.value,
        MailHistoryBounceSubType.ON_ACCOUNT_SUPPRESSION_LIST.value,
        MailHistoryBounceSubType.CONTENT_REJECTED.value,
        MailHistoryBounceSubType.ATTACHMENT_REJECTED.value,
    ]
    query = (
        select(
            func.count().label("total"),
            func.count(
                case(
                    (
                        or_(
                            SequenceMailHistory.status == MailHistoryStatus.SENT,
                            SequenceMailHistory.status == MailHistoryStatus.OPENED,
                        ),
                        1,
                    ),
                    else_=None,
                )
            ).label("delivered_count"),
            func.count(
                case(
                    (SequenceMailHistory.status == MailHistoryStatus.OPENED, 1),
                    else_=None,
                )
            ).label("opened_count"),
            func.count(
                case(
                    (
                        (
                            (SequenceMailHistory.status == MailHistoryStatus.BOUNCED)
                            & (SequenceMailHistory.bounce_sub_type.in_(spam_subtype))
                        ),
                        1,
                    ),
                    else_=None,
                )
            ).label("spam_blocked_count"),
            func.count(
                case(
                    (
                        (
                            (SequenceMailHistory.status == MailHistoryStatus.BOUNCED)
                            & (SequenceMailHistory.bounce_sub_type.not_in(spam_subtype))
                        ),
                        1,
                    ),
                    else_=None,
                )
            ).label("bounced_count"),
            func.count(
                case(
                    (SequenceMailHistory.status == MailHistoryStatus.REPLIED, 1),
                    else_=None,
                )
            ).label("replied_count"),
            func.count(
                case(
                    (SequenceMailHistory.status == MailHistoryStatus.FAILED, 1),
                    else_=None,
                )
            ).label("not_sent_count"),
            func.count(
                case(
                    (SequenceMailHistory.status == MailHistoryStatus.OPT_OUT, 1),
                    else_=None,
                )
            ).label("opt_out_count"),
        )
        .join(
            SequenceCampaignStep,
            SequenceCampaignStep.id == SequenceMailHistory.sequence_step_id,
        )
        .where(
            SequenceMailHistory.sequence_campaign_id == sequence_campaign_id,
            SequenceMailHistory.deleted_at.is_(None),
            SequenceMailHistory.status.not_in(
                [MailHistoryStatus.SKIPPED, MailHistoryStatus.SCHEDULED]
            ),
            SequenceCampaignStep.step_type.in_(
                [StepType.MAIL_AUTO, StepType.MAIL_MANUAL]
            ),
        )
    )
    condition = ""
    if sequence_step_id:
        query = query.where(SequenceMailHistory.sequence_step_id == sequence_step_id)
        condition = f"AND v.sequence_step_id = {sequence_step_id}"
    result = db.exec(query).first()
    (
        total,
        delivered_count,
        opened_count,
        spam_blocked_count,
        bounced_count,
        replied_count,
        not_sent_count,
        opt_out_count,
    ) = result
    params = {
        "sequence_campaign_id": sequence_campaign_id,
        "status": MailHistoryStatus.SCHEDULED,
    }
    result = (
        db.exec(
            text(
                f"""SELECT COUNT(*) AS scheduled_count
            FROM {MAIL_HISTORY_VIEW_NAME} v
            JOIN sequence_campaign_steps scs
            ON v.sequence_step_id = scs.id
            WHERE v.sequence_campaign_id = :sequence_campaign_id
            AND v.status = :status
            AND scs.step_type IN ('MAIL_MANUAL', 'MAIL_AUTO')
            {condition}
            """
            ),
            params=params,
        )
        .mappings()
        .first()
    )
    scheduled_count = result["scheduled_count"]
    total += scheduled_count
    return {
        "total": total,
        "bounced_count": bounced_count,
        "spam_blocked_count": spam_blocked_count,
        "scheduled_count": scheduled_count,
        "delivered_count": delivered_count,
        "reply_count": replied_count,
        "open_count": opened_count,
        "not_sent_count": not_sent_count,
        "opt_out_count": opt_out_count,
    }


def get_sequence_owner(db, current_user):
    result = db.exec(
        select(User.id, User.name).where(
            User.team_id == current_user.team_id,
            User.deleted_at.is_(None),
        )
    )
    owners = []
    for row in result.mappings().all():
        row_dict = dict(row)
        row_dict["is_current_user"] = row["id"] == current_user.id
        owners.append(ListingSequenceOwnerResponse(**row_dict))
    return owners


def get_contact_stat(sequence_campaign_id, sequence_step_id, db):
    query = select(
        func.count().label("total"),
        func.count(
            case((SequenceCampaignContacts.status == "ACTIVE", 1), else_=None)
        ).label("active_count"),
        func.count(
            case((SequenceCampaignContacts.status == "PAUSE", 1), else_=None)
        ).label("pause_count"),
        func.count(
            case((SequenceCampaignContacts.status == "BOUNCED", 1), else_=None)
        ).label("bounced_count"),
        func.count(
            case((SequenceCampaignContacts.status == "NOT_SENT", 1), else_=None)
        ).label("not_sent_count"),
        func.count(
            case((SequenceCampaignContacts.status == "FINISH", 1), else_=None)
        ).label("finished_count"),
    ).where(
        SequenceCampaignContacts.sequence_campaign_id == sequence_campaign_id,
        SequenceCampaignContacts.deleted_at.is_(None),
    )
    if sequence_step_id:
        query = (
            query.join(
                SequenceCampaignStep, SequenceCampaignStep.id == sequence_step_id
            )
            .join(
                SequenceContact,
                (SequenceContact.id == SequenceCampaignContacts.sequence_contact_id)
                & (SequenceContact.sequence_campaign_id == sequence_campaign_id),
            )
            .where(SequenceContact.current_step == SequenceCampaignStep.order)
        )
    result = db.exec(query).first()
    (
        total,
        active_count,
        paused_count,
        bounced_count,
        not_sent_count,
        finished_count,
    ) = result
    return {
        "total": total,
        "active_count": active_count,
        "paused_count": paused_count,
        "not_sent_count": not_sent_count,
        "bounced_count": bounced_count,
        "finished_count": finished_count,
    }


def list_campaign_service(
    db: Session,
    current_user: UserBase,
    params: ListingCampaignRequest,
    owner_id: Optional[List[int]] = Query(default=None),
):
    try:
        query = (
            select(SequenceCampaign, User.name.label("owner_name"), User.avatar_path)
            .join(User, SequenceCampaign.owner_id == User.id, isouter=True)
            .where(
                SequenceCampaign.team_id == current_user.team_id,
            )
        )

        if params.name:
            query = query.where(SequenceCampaign.name.ilike(f"%{params.name}%"))
        if owner_id:
            query = query.where(SequenceCampaign.owner_id.in_(owner_id))
        if params.is_active:
            query = query.where(SequenceCampaign.is_active.is_(params.is_active))
        if params.status:
            if params.status == SequenceCampaignStatusEnum.ACTIVE:
                query = query.where(
                    SequenceCampaign.is_active.is_(True)
                    & (SequenceCampaign.deleted_at.is_(None))
                )
            elif params.status == SequenceCampaignStatusEnum.INACTIVE:
                query = query.where(
                    SequenceCampaign.is_active.is_(False)
                    & (SequenceCampaign.deleted_at.is_(None))
                )
            elif params.status == SequenceCampaignStatusEnum.ACTIVE_AND_INACTIVE:
                query = query.where(
                    (
                        SequenceCampaign.is_active.is_(True)
                        | SequenceCampaign.is_active.is_(False)
                    )
                    & (SequenceCampaign.deleted_at.is_(None))
                )
            elif params.status == SequenceCampaignStatusEnum.ARCHIVED:
                query = query.where(SequenceCampaign.deleted_at.is_not(None))

        total_query = query.with_only_columns(func.count()).order_by(None)

        total_result = db.exec(total_query).first()
        total = total_result[0] if total_result else 0

        if params.order_by == SequenceCampaignOrderEnum.LAST_USED:
            column = getattr(SequenceCampaign, "updated_at", None)
        else:
            column = getattr(SequenceCampaign, params.order_by, None)

        if column:
            query = query.order_by(
                desc(column)
                if params.order_type == SequenceCampaignOrderTypeEnum.DESC
                else asc(column)
            )
        else:
            raise HTTPException(status_code=400)
        query = (
            query.limit(params.per_page)
            .offset((params.page - 1) * params.per_page)
            .order_by(SequenceCampaign.id.desc())
        )
        result = db.exec(query).all()

        ret = []
        for campaign, owner_name, owner_avatar in result:
            item = dict(campaign)
            item["statistic"] = {
                "contact_statistic": get_contact_stat(campaign.id, None, db),
            }
            item["owner_name"] = owner_name
            item["owner_avatar"] = (
                media_service.get_presigned_url(owner_avatar) if owner_avatar else None
            )
            ret.append(item)

        return ret, total
    except Exception as e:
        db.rollback()
        raise e


def list_campaign_add_contacts_service(
    db: Session,
    current_user: UserBase,
    params: ListingImportContactsRequest,
):
    try:
        query = (
            select(SequenceCampaign, User.name.label("owner_name"), User.avatar_path)
            .join(User, SequenceCampaign.owner_id == User.id, isouter=True)
            .where(
                SequenceCampaign.team_id == current_user.team_id,
                SequenceCampaign.deleted_at.is_(None),
            )
        )

        if params.name:
            query = query.where(SequenceCampaign.name.ilike(f"%{params.name}%"))

        total_query = query.with_only_columns(func.count()).order_by(None)

        total_result = db.exec(total_query).first()
        total = total_result[0] if total_result else 0

        query = (
            query.limit(params.per_page)
            .offset((params.page - 1) * params.per_page)
            .order_by(SequenceCampaign.id.desc())
        )
        result = db.exec(query).all()

        ret = []
        for campaign in result:
            item = {"id": campaign[0].id, "name": campaign[0].name}
            ret.append(item)

        return ret, total
    except Exception as e:
        db.rollback()
        raise e


def get_campaign_service(db: Session, current_user: UserBase, campaign_id: int):
    campaign = db.exec(
        select(SequenceCampaign).where(
            SequenceCampaign.id == campaign_id,
            SequenceCampaign.deleted_at.is_(None),
            SequenceCampaign.team_id == current_user.team_id,
        )
    ).first()
    if not campaign:
        raise NotFoundException("Campaign not found")
    ret = dict(campaign)
    ret["statistic"] = {
        "email_statistic": get_email_stat(campaign.id, None, db),
        "contact_statistic": get_contact_stat(campaign.id, None, db),
        "linkedin_statistic": get_linkedin_histories_statistics_service(
            db, campaign.id, current_user, None
        ),
    }

    exist_persons = db.exec(
        select(SequenceContact)
        .join(
            SequenceCampaignContacts,
            SequenceContact.id == SequenceCampaignContacts.sequence_contact_id,
        )
        .where(
            SequenceCampaignContacts.sequence_campaign_id == campaign_id,
            SequenceCampaignContacts.deleted_at.is_(None),
            SequenceCampaignContacts.status.not_in(
                [StatusEnum.FINISH.value, StatusEnum.PAUSE.value]
            ),
        )
    ).all()

    if len(exist_persons):
        ret["have_contact"] = True

    steps = db.exec(
        select(SequenceCampaignStep)
        .where(
            SequenceCampaignStep.sequence_campaign_id == campaign_id,
            SequenceCampaignStep.deleted_at.is_(None),
        )
        .order_by(asc(SequenceCampaignStep.order))
    ).all()

    # Create tasks for the first step if it is a manual mail step
    if (
        len(steps) > 0
        and campaign.is_active
        and steps[0].step_type == StepType.MAIL_MANUAL
    ):
        first_step = steps[0]
        exist_tasks = db.exec(
            select(SequenceTask).where(
                SequenceTask.sequence_campaign_id == campaign_id,
                SequenceTask.sequence_step_id == first_step.id,
                SequenceTask.deleted_at.is_(None),
            )
        ).all()
        exist_task_person = {exist_person.id: False for exist_person in exist_persons}

        for task in exist_tasks:
            exist_task_person[task.sequence_person_id] = True

        for person in exist_persons:
            if exist_task_person.get(person.id):
                continue
            if not person.current_step == 1:
                continue
            due_date = get_due_date(first_step)
            valid, schedule = validate_campaign_on_sending_window(
                db, first_step.sequence_campaign_id, due_date
            )
            if not valid:
                if schedule:
                    due_date = schedule
            task = SequenceTask(
                team_id=campaign.team_id,
                user_id=campaign.created_by,
                sequence_campaign_id=campaign.id,
                sequence_step_id=first_step.id,
                task_type=TaskType.EMAIL,
                sequence_person_id=person.id,
                due_date=due_date,
                priority=first_step.priority,
                status=TaskStatus.SCHEDULED,
                created_at=datetime.now(),
                created_by=campaign.created_by,
            )
            db.add(task)

    template_ids = [
        step.content_template_id
        for step in steps
        if step.content_template_id is not None
    ]

    templates = db.exec(
        select(SequenceStepContentTemplate).where(
            SequenceStepContentTemplate.deleted_at.is_(None),
            SequenceStepContentTemplate.id.in_(template_ids),
        )
    ).all()
    template_mapping = {template.id: dict(template) for template in templates}
    items = db.exec(
        select(SequenceStepContentItem).where(
            SequenceStepContentItem.step_content_template_id.in_(template_ids)
        )
    ).all()
    items_mapping = defaultdict(list)
    for i in items:
        items_mapping[i.step_content_template_id].append(i.dict())
    campaign_steps = []
    for index, step in enumerate(steps):
        item = dict(step)
        content_template = template_mapping.get(step.content_template_id)
        item["content_template"] = content_template
        item["template_items"] = items_mapping.get(step.content_template_id, [])
        item["statistic"] = {
            "email_statistic": get_email_stat(campaign.id, step.id, db),
            "contact_statistic": get_contact_stat(campaign.id, step.id, db),
            "linkedin_statistic": get_linkedin_histories_statistics_service(
                db, campaign.id, current_user, step.id
            ),
        }
        item["content_template_id"] = step.content_template_id
        item["total_days"] = step.total_days
        item["is_active_not_allowed"] = False
        if item["step_type"] == StepType.LINKEDIN_AUTO_MESSAGE:
            if len(item["template_items"]) == 0:
                item["is_active_not_allowed"] = True
            if len(item["template_items"]) == 1:
                first_item = item["template_items"][0]
                if first_item.get("type") == ContentItemsType.TEXT:
                    if not content_template.get("content"):
                        item["is_active_not_allowed"] = True
                elif not first_item.get("file_path"):
                    item["is_active_not_allowed"] = True
        if (
            item["step_type"] == StepType.MAIL_AUTO
            or item["step_type"] == StepType.MAIL_MANUAL
        ):
            if content_template.get("content_type") == ContentType.MAIL:
                if not content_template.get("title"):
                    item["is_active_not_allowed"] = True
        campaign_steps.append(item)
    ret["steps"] = campaign_steps
    ret["is_first_active"] = campaign.is_first_active
    db.commit()
    return ret
