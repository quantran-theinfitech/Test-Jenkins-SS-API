# flake8: noqa: E501
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, case, func, or_, text
from sqlmodel import Session, asc, col, desc, select

from app.api.v1.schemas.sequence.persons import (
    SequencePersonStageStatistic,
    SortField,
    SortOrder,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.mail_histories.verify_campaign_permisstion_service import (
    verify_campaign_permission,
)
from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.campaign_import import (
    SequenceCampaignImport,
    UploadProcessStatus,
)
from app.models.sequence.contact import SequenceContact, SequencePersonStage
from app.models.sequence.linkedin_account import LinkedInAccount
from app.models.sequence.mail_alias_setting import (
    SequenceMailAliasSetting,
    SettingOption,
)
from app.models.sequence.mail_history import MAIL_HISTORY_VIEW_NAME
from app.models.sequence.person_statistics import SequencePersonStatistics
from app.models.sequence.step import SequenceCampaignStep


def listing_sequence_persons_service(
    db: Session,
    sequence_campaign_id: int,
    page: int,
    per_page: int,
    current_user: UserBase,
    mail_senders: Optional[List[str]] = None,
    # alias_emails: Optional[List[str]] = None,
    current_step: Optional[List[int]] = None,
    order: Optional[SortOrder] = SortOrder.DESC,
    field: Optional[SortField] = SortField.CREATED_AT,
    keyword: Optional[str] = None,
    status: Optional[List[StatusEnum]] = None,
    linkedin_senders: Optional[List[str]] = None,
):
    verify_campaign_permission(db, current_user, sequence_campaign_id)
    condition = [
        SequenceContact.sequence_campaign_id == sequence_campaign_id,
        SequenceContact.deleted_at.is_(None),
    ]
    if keyword:
        search_name = keyword
        if search_name:
            array_ilike_condition = text(
                """
                EXISTS(SELECT 1 FROM unnest(company_name)
                AS company WHERE company ILIKE :search)
                """
            )
            condition.append(
                or_(
                    SequenceContact.name.ilike(f"%{search_name}%"),
                    array_ilike_condition.bindparams(search=f"%{search_name}%"),
                )
            )
    # if mails:
    #     condition.append(
    #         and_(
    #             col(SequenceMailAliasSetting.mailbox_id).in_(mails),
    #             col(SequenceMailAliasSetting.setting_option) == SettingOption.CONTACT,
    #         )
    #     )
    #     if alias_emails:
    #         condition.append(
    #             col(SequenceMailAliasSetting.mailbox_alias_id).in_(alias_emails)
    #         )
    if status:
        condition.append(col(SequenceCampaignContacts.status).in_(status))
    if current_step:
        current_step = db.exec(
            select(SequenceCampaignStep.order).where(
                SequenceCampaignStep.id.in_(current_step)
            )
        ).all()
        if current_step:
            condition.append(col(SequenceContact.current_step).in_(current_step))

    def get_contact_ids_by_senders(field: str, values: list):
        query_view = text(
            f"""
            SELECT v.sequence_contact_id
            FROM {MAIL_HISTORY_VIEW_NAME} v
            WHERE v.{field} = ANY(:values)
            """
        )
        result = db.execute(query_view, {"values": values}).all()
        return [row[0] for row in result]

    if mail_senders:
        contact_ids = get_contact_ids_by_senders("email_from", mail_senders)
        condition.append(col(SequenceContact.id).in_(contact_ids))

    if linkedin_senders:
        account_ids = db.exec(
            select(LinkedInAccount.id).where(
                LinkedInAccount.public_identifier.in_(linkedin_senders)
            )
        ).all()
        contact_ids = get_contact_ids_by_senders(
            "sequence_linkedin_account_id", account_ids
        )
        condition.append(col(SequenceContact.id).in_(contact_ids))

    sort_field_mapping = {
        "created_at": SequenceContact.created_at,
        "last_activity": SequencePersonStatistics.last_activity,
        "email_last_opened_at": SequencePersonStatistics.email_last_opened_at,
        "email_last_clicked_at": SequencePersonStatistics.email_last_clicked_at,
        "times_opened": SequencePersonStatistics.times_opened,
        "times_clicked": SequencePersonStatistics.times_clicked,
        "name": SequenceContact.name,
        "company_name": SequenceContact.company_name,
    }
    if order == SortOrder.DESC:
        order_statement = desc(sort_field_mapping[field]).nulls_last()
    else:
        order_statement = asc(sort_field_mapping[field]).nulls_last()

    sequence_import_files = db.exec(
        select(SequenceCampaignImport).where(
            SequenceCampaignImport.sequence_campaign_id == sequence_campaign_id,
            SequenceCampaignImport.upload_process_status
            == UploadProcessStatus.IN_PROGRESS.value,
            SequenceCampaignImport.deleted_at.is_(None),
        )
    ).all()
    upload_process = UploadProcessStatus.FINISHED.value
    for import_file in sequence_import_files:
        if import_file.upload_process_status == UploadProcessStatus.IN_PROGRESS.value:
            if import_file.created_at < datetime.now() - timedelta(hours=3):
                import_file.upload_process_status = UploadProcessStatus.FAILED.value
                continue
            upload_process = UploadProcessStatus.IN_PROGRESS.value
    db.commit()

    sequence_persons = (
        db.query(SequenceContact, SequencePersonStatistics)
        .outerjoin(
            SequencePersonStatistics,
            SequenceContact.id == SequencePersonStatistics.sequence_person_id,
        )
        .outerjoin(
            SequenceCampaignContacts,
            SequenceContact.id == SequenceCampaignContacts.sequence_contact_id,
        )
        .outerjoin(
            SequenceMailAliasSetting,
            SequenceContact.id == SequenceMailAliasSetting.sequence_person_id,
        )
        .filter(*condition)
        .order_by(order_statement, asc(SequenceContact.id))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    total = (
        db.query(SequenceContact.id)
        .outerjoin(
            SequencePersonStatistics,
            SequenceContact.id == SequencePersonStatistics.sequence_person_id,
        )
        .outerjoin(
            SequenceCampaignContacts,
            SequenceContact.id == SequenceCampaignContacts.sequence_contact_id,
        )
        .outerjoin(
            SequenceMailAliasSetting,
            SequenceContact.id == SequenceMailAliasSetting.sequence_person_id,
        )
        .filter(*condition)
        .count()
    )
    persons_with_status = []
    for person in sequence_persons:
        condition = [
            SequenceCampaignContacts.sequence_contact_id == person.SequenceContact.id,
            SequenceCampaignContacts.sequence_campaign_id == sequence_campaign_id,
        ]
        query = select(SequenceCampaignContacts.status).where(*condition)
        status = db.exec(query).first()

        persons_with_status.append(
            {
                "person": {
                    **person.SequenceContact.__dict__,
                },
                "person_statistics": {
                    **(
                        person.SequencePersonStatistics.__dict__
                        if person.SequencePersonStatistics
                        else {}
                    ),
                },
                "status": status,
            }
        )
    return persons_with_status, total, upload_process


def listing_sequence_persons_count(
    db: Session, sequence_campaign_id: int, step_ids: Optional[List[int]]
):
    condition = [SequenceCampaignStep.id.in_(step_ids)]
    query = select(SequenceCampaignStep.order).where(*condition)
    current_step = db.exec(query).all()
    condition = [
        SequenceContact.sequence_campaign_id == sequence_campaign_id,
        SequenceContact.deleted_at.is_(None),
    ]
    query = db.query(SequenceContact).filter(*condition)
    if current_step:
        query = query.filter(SequenceContact.current_step.in_(current_step))
    count = query.count()
    return count


def get_sequence_person_stage_count(
    db: Session, sequence_campaign_id: int, current_user: UserBase
):
    verify_campaign_permission(db, current_user, sequence_campaign_id)
    query = select(
        func.count().label("total"),
        func.count(
            case(
                (SequenceContact.stage == SequencePersonStage.COLD, 1),
                else_=None,
            )
        ).label("cold_count"),
        func.count(
            case(
                (SequenceContact.stage == SequencePersonStage.APPROACHING, 1),
                else_=None,
            )
        ).label("approaching_count"),
        func.count(
            case(
                (SequenceContact.stage == SequencePersonStage.UNRESPONSIVE, 1),
                else_=None,
            )
        ).label("unresponsive_count"),
        func.count(
            case(
                (SequenceContact.stage == SequencePersonStage.BAD_DATA, 1),
                else_=None,
            )
        ).label("bad_data_count"),
        func.count(
            case(
                (
                    SequenceContact.stage == SequencePersonStage.DO_NOT_CONTACT,
                    1,
                ),
                else_=None,
            )
        ).label("do_not_contact_count"),
        func.count(
            case(
                (SequenceContact.stage == SequencePersonStage.REPLIED, 1),
                else_=None,
            )
        ).label("replied_count"),
    ).where(
        SequenceContact.sequence_campaign_id == sequence_campaign_id,
        SequenceContact.deleted_at.is_(None),
    )
    result = db.exec(query).first()
    (
        total,
        cold_count,
        approaching_count,
        unresponsive_count,
        bad_data_count,
        do_not_contact_count,
        replied_count,
    ) = result
    return SequencePersonStageStatistic(
        total=total,
        cold_count=cold_count,
        approaching_count=approaching_count,
        unresponsive_count=unresponsive_count,
        bad_data_count=bad_data_count,
        do_not_contact_count=do_not_contact_count,
        replied_count=replied_count,
    )
