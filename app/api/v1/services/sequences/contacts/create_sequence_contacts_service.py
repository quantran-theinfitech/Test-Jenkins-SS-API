from datetime import datetime
from itertools import islice

from sqlmodel import Session, or_, select, update

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.person_collections import TypeDownloadPerson
from app.api.v1.schemas.sequence.campaigns import AddSequenceContactRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.person_collections.create_person_collection_service import (
    get_list_person_download,
)
from app.db import engine
from app.models.person import Person
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.contact import (
    ContactType,
    SequenceContact,
    SequencePersonStage,
)
from app.models.sequence.step import SequenceCampaignStep, StepType
from app.models.team import PlanCode, Team
from app.models.team_credit import ServiceCode
from app.models.team_person import TeamPerson
from utils.credit_utils import is_enough_credit


def chunked(iterable, size: int):
    """Yield successive chunks of given size from iterable."""
    it = iter(iterable)
    while chunk := list(islice(it, size)):
        yield chunk


FIELD_MAP = {
    "name": "name",
    "role_name": "role_name",
    "email": "email",
    "linkedin_url": "linkedin_url",
    "twitter_url": "twitter_url",
    "github_url": "github_url",
    "note_url": "note_url",
    "fb_url": "fb_url",
    "wantedly_url": "wantedly_url",
    "skills": "skills",
    "corporate_number": "corporate_number",
    "company_name": "company_name",
    "wantedly_id": "wantedly_id",
    "address": "address",
    "linkedin_internal_id": "linkedin_internal_id",
    "intro": "intro",
    "bio": "bio",
    "role_code": "role_code",
    "role_group_codes": "role_group_codes",
}

# Những field cần giữ nguyên list
LIST_FIELDS = {"role_name", "company_name", "corporate_number"}


async def prepare_sequence_contacts(
    request: AddSequenceContactRequest,
    current_user: UserBase,
    # cross_search_service: CrossSearchService,
    # search_condition: Optional[SearchCrossRequest] = SearchCrossRequest(),
    # listing_plan_code: PlanCode = Depends(get_plan_code()),
):
    db = Session(engine)
    team = db.get(Team, current_user.team_id)
    if not team:
        raise NotFoundException(detail="team.teamNotFound")
    unlocked_person_list = db.exec(
        select(TeamPerson.person_uuid).where(TeamPerson.team_id == team.id)
    ).all()
    # mở khóa person
    if request.type_download_person == TypeDownloadPerson.CREDIT:
        get_list_person_download(
            db, current_user, request.type_download_person, request.contact_uuids
        )
    elif team.listing_plan_code != PlanCode.UNLIMITED:
        request.contact_uuids = [
            contact_uuid
            for contact_uuid in request.contact_uuids
            if contact_uuid in unlocked_person_list
        ]

    exist_seq = db.exec(
        select(SequenceCampaign).where(
            SequenceCampaign.id == request.sequence_campaign_id,
            SequenceCampaign.deleted_at.is_(None),
            SequenceCampaign.team_id == current_user.team_id,
        )
    ).first()
    if not exist_seq:
        raise NotFoundException(detail="sequence.SequenceNotFound")

    exist_contacts = db.exec(
        select(SequenceContact.uuid).where(
            SequenceContact.sequence_campaign_id == request.sequence_campaign_id,
            SequenceContact.deleted_at.is_(None),
        )
    ).all()
    exist_set = set(exist_contacts)

    to_add = [pid for pid in request.contact_uuids if pid not in exist_set]
    if not to_add:
        return

    # Lấy thông tin person từ cross_search
    # person_contacts, _, _ = await cross_search_service.search(
    #     request=search_condition,
    #     target=SearchTarget.PERSON,
    #     current_user=current_user,
    #     page=1,
    #     per_page=9000000,
    #     listing_plan_code=listing_plan_code,
    # )

    if request.is_include_incompleted_contacts is True:
        person_contacts = db.exec(select(Person).where(Person.uuid.in_(to_add))).all()
    else:
        person_contacts = db.exec(
            select(Person).where(
                Person.uuid.in_(to_add),
                or_(Person.email.is_not(None), Person.linkedin_url.is_not(None)),
            )
        ).all()
    if not person_contacts:
        raise NotFoundException(detail="person.PersonNotFound")
    return {
        "exist_seq": exist_seq,
        "to_add": to_add,
        "contact_map": {person.uuid: person for person in person_contacts},
        # "contact_map": {person["uuid"]: person for person in person_contacts},
        "current_user": current_user,
    }


def process_sequence_contacts(data: dict):
    db = Session(engine)
    exist_seq = data["exist_seq"]
    to_add = data["to_add"]
    contact_map = data["contact_map"]
    current_user = data["current_user"]

    CHUNK_SIZE = 500
    if CHUNK_SIZE > len(to_add):
        CHUNK_SIZE = len(to_add)

    if not is_enough_credit(db, current_user.team_id, 1, ServiceCode.LINKEDIN_MSG):
        db.exec(
            update(SequenceCampaignStep)
            .where(
                SequenceCampaignStep.sequence_campaign_id == exist_seq.id,
                SequenceCampaignStep.step_type.in_(
                    [
                        StepType.LINKEDIN_AUTO_MESSAGE,
                        StepType.LINKEDIN_CONNECTION_REQUEST,
                        StepType.LINKEDIN_VIEW_PROFILE,
                    ]
                ),
                SequenceCampaignStep.deleted_at.is_(None),
            )
            .values(is_active=False)
        )
    elif not is_enough_credit(db, current_user.team_id, 1, ServiceCode.EMAIL):
        db.exec(
            update(SequenceCampaignStep)
            .where(
                SequenceCampaignStep.sequence_campaign_id == exist_seq.id,
                SequenceCampaignStep.step_type.in_(
                    [StepType.MAIL_AUTO, StepType.MAIL_MANUAL]
                ),
            )
            .values(is_active=False)
        )

    for batch in chunked(to_add, CHUNK_SIZE):
        new_contacts = []

        for pid in batch:
            contact = contact_map.get(pid)
            if not contact:
                continue

            values = {}
            for model_field, contact_key in FIELD_MAP.items():
                # val = contact.get(contact_key)
                val = getattr(contact, contact_key, None)
                if model_field in LIST_FIELDS:
                    if val is None:
                        val = []
                    elif not isinstance(val, list):
                        val = [val]
                else:
                    if isinstance(val, list):
                        val = val[0] if val else None
                values[model_field] = val

            new_contacts.append(
                SequenceContact(
                    uuid=pid,
                    sequence_campaign_id=exist_seq.id,
                    target_type=ContactType.PERSON,
                    current_step=1,
                    stage=SequencePersonStage.COLD,
                    created_at=datetime.now(),
                    created_by=current_user.id,
                    **values,
                )
            )

        # Lưu contacts và flush để có id
        db.add_all(new_contacts)
        db.flush()

        # Dùng bulk_save_objects để insert nhanh campaign_contacts
        new_campaign_contacts = [
            SequenceCampaignContacts(
                sequence_campaign_id=new_contact.sequence_campaign_id,
                sequence_contact_id=new_contact.id,
                status=StatusEnum.ACTIVE if exist_seq.is_active else StatusEnum.PAUSE,
                created_at=datetime.now(),
                created_by=current_user.id,
                time_resumed=datetime.now() if exist_seq.is_active else None,
            )
            for new_contact in new_contacts
        ]

        db.bulk_save_objects(new_campaign_contacts)

    db.commit()
