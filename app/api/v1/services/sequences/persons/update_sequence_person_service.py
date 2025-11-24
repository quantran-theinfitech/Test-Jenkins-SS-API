# flake8: noqa: C901
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select, update

from app.api.v1.schemas.sequence.persons import (
    ChangeSequencePersonMailbox,
    UpdateSequencePersonRequest,
    UpdateSequencePersonStageRequest,
)
from app.api.v1.schemas.users import UserBase
from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.contact import SequenceContact
from app.models.sequence.mail_alias_setting import (
    SequenceMailAliasSetting,
    SettingOption,
)
from app.models.sequence.mail_history import MailHistoryStatus


def update_sequence_person_service(
    sequence_campaign_id: int,
    person_id: int,
    request: UpdateSequencePersonRequest,
    db: Session,
    current_user: UserBase,
):
    contact_email = None
    contact_linkedin = None

    if request.email:
        contact_email = db.exec(
            select(SequenceContact).where(
                SequenceContact.sequence_campaign_id == sequence_campaign_id,
                SequenceContact.email == request.email,
                SequenceContact.deleted_at.is_(None),
                SequenceContact.id != person_id,
            )
        ).first()

    if request.linkedin_url:
        contact_linkedin = db.exec(
            select(SequenceContact).where(
                SequenceContact.sequence_campaign_id == sequence_campaign_id,
                SequenceContact.linkedin_url == request.linkedin_url,
                SequenceContact.deleted_at.is_(None),
                SequenceContact.id != person_id,
            )
        ).first()

    if contact_email and contact_linkedin:
        raise HTTPException(
            status_code=400, detail="sequence.emailAndLinkedinAlreadyExist"
        )
    elif contact_email:
        raise HTTPException(status_code=400, detail="sequence.emailAlreadyExists")
    elif contact_linkedin:
        raise HTTPException(status_code=400, detail="sequence.linkedinAlreadyExists")

    update_values = request.dict(exclude_unset=True)
    update_values["updated_at"] = datetime.now()
    update_values["updated_by"] = current_user.id
    db.execute(
        update(SequenceContact)
        .where(
            SequenceContact.id == person_id,
            SequenceContact.sequence_campaign_id == sequence_campaign_id,
        )
        .values(update_values)
    )
    if request.email:
        db.execute(
            f"""
            UPDATE sequence_mail_histories AS smh
            SET to_address = :email
            FROM sequence_campaign_steps AS scs
            WHERE smh.sequence_step_id = scs.id
            AND smh.sequence_contact_id = :person_id
            AND smh.sequence_campaign_id = :sequence_campaign_id
            AND smh.status = :scheduled
            AND scs.step_type IN ('MAIL_AUTO', 'MAIL_MANUAL')
            """,
            {
                "email": request.email,
                "person_id": person_id,
                "sequence_campaign_id": sequence_campaign_id,
                "scheduled": MailHistoryStatus.SCHEDULED,
            },
        )
    if request.linkedin_url:
        db.execute(
            f"""
            UPDATE sequence_mail_histories AS smh
            SET to_address = :linkedin_url
            FROM sequence_campaign_steps AS scs
            WHERE smh.sequence_step_id = scs.id
            AND smh.sequence_contact_id = :person_id
            AND smh.sequence_campaign_id = :sequence_campaign_id
            AND smh.status = :scheduled
            AND scs.step_type IN ('LINKEDIN_AUTO_MESSAGE', 'LINKEDIN_CONNECTION_REQUEST', 'LINKEDIN_VIEW_PROFILE')
            """,
            {
                "linkedin_url": request.linkedin_url,
                "person_id": person_id,
                "sequence_campaign_id": sequence_campaign_id,
                "scheduled": MailHistoryStatus.SCHEDULED,
            },
        )
    db.commit()
    return {"success": True}


def update_sequence_person_stage_service(
    sequence_campaign_id: int,
    request: UpdateSequencePersonStageRequest,
    db: Session,
    current_user: UserBase,
):
    condition = [
        SequenceContact.sequence_campaign_id == sequence_campaign_id,
        SequenceContact.id.in_(request.sequence_person_ids),
    ]
    query = select(SequenceContact).where(*condition)
    persons = db.exec(query).all()
    if persons == []:
        raise HTTPException(status_code=404, detail="sequence.personNotFound")
    for person in persons:
        if person.status == StatusEnum.FINISH.value:
            continue
        person.stage = request.stage
        person.updated_at = datetime.now()
        person.updated_by = current_user.id
        db.add(person)
    db.commit()
    for person in persons:
        db.refresh(person)


def change_sequence_person_mailbox_service(
    sequence_campaign_id: int, request: ChangeSequencePersonMailbox, db: Session
):
    result = True  # True: all contacts finished or bounced, False: some contacts not finished
    for person_id in request.sequence_person_ids:
        person = db.exec(
            select(SequenceCampaignContacts).where(
                SequenceCampaignContacts.sequence_contact_id == person_id,
                SequenceCampaignContacts.sequence_campaign_id == sequence_campaign_id,
                SequenceCampaignContacts.deleted_at.is_(None),
            )
        ).first()
        if person and (
            person.status != StatusEnum.FINISH and person.status != StatusEnum.BOUNCED
        ):
            result = False
            mail_alias_setting = SequenceMailAliasSetting(
                mailbox_id=request.mailbox_id,
                mailbox_alias_id=request.mailbox_alias_id,
                setting_option=SettingOption.CONTACT,
                sequence_person_id=person_id,
                sequence_campaign_id=sequence_campaign_id,
            )
            db.add(mail_alias_setting)

    db.commit()

    return result
