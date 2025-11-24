from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.person_collections import TypeDownloadPerson
from app.api.v1.schemas.sequence.campaigns import (
    ContactPreviewInfo,
    ContactStatisticsBase,
    GetContactUuidsRequest,
    GetPreviewContactResponse,
)
from app.api.v1.schemas.users import UserBase
from app.models.person import Person
from app.models.person_collection import PersonCollection
from app.models.person_collection_item import PersonCollectionItem
from app.models.sequence.contact import SequenceContact
from app.models.team import PlanCode, Team
from app.models.team_person import TeamPerson


def get_sequence_contact_service(
    sequence_campaign_id: int,
    request: GetContactUuidsRequest,
    db: Session,
    current_user: UserBase,
) -> GetPreviewContactResponse:
    """
    return
        new_contacts: ContactStatisticsBase (new contact)
        restored_contacts: ContactStatisticsBase (removed contact)
        incomplete_contacts: ContactStatisticsBase (email or linkedin_url is None)
        duplicate_contacts: ContactStatisticsBase (existing contact in sequence)
        total: int
    """
    # Nếu là tài khoản unlimited thì không có trong TeamPerson
    team = db.get(Team, current_user.team_id)
    if request.collection_list_id:
        team = db.get(Team, current_user.team_id)
        collection = db.get(PersonCollection, request.collection_list_id)
        if collection.team_id != team.id:
            raise NotFoundException(detail="collection.NotFound")
        preview_uuids_list = db.exec(
            select(PersonCollectionItem.person_uuid).where(
                PersonCollectionItem.collection_id == request.collection_list_id,
                PersonCollectionItem.deleted_at.is_(None),
            )
        ).all()
    # Nếu chọn add những persons đã mở khóa
    elif (
        request.type_download_person == TypeDownloadPerson.DOWNLOADED
        and team.listing_plan_code != PlanCode.UNLIMITED
    ):

        # Nếu chọn add những persons đã mở khóa
        preview_uuids_list = db.exec(
            select(TeamPerson.person_uuid)
            .where(
                TeamPerson.team_id == current_user.team_id,
                TeamPerson.person_uuid.in_(request.contact_uuids),
            )
            .distinct(TeamPerson.person_uuid)
        ).all()
    else:
        preview_uuids_list = request.contact_uuids

    all_existed_contacts = db.exec(
        select(SequenceContact.uuid, SequenceContact.deleted_at).where(
            SequenceContact.sequence_campaign_id == sequence_campaign_id
        )
    ).all()

    existing_set = {
        uuid for uuid, deleted_at in all_existed_contacts if deleted_at is None
    }
    removed_set = {
        uuid for uuid, deleted_at in all_existed_contacts if deleted_at is not None
    }
    # lay thong tin contact duoc chon
    selected_contacts = db.exec(
        select(Person).where(
            Person.uuid.in_(preview_uuids_list), Person.deleted_at.is_(None)
        )
    ).all()

    incomplete_contacts_data = []
    duplicate_contacts_data = []
    restored_contacts_data = []
    new_contacts_data = []

    for contact in selected_contacts:
        if contact.uuid in existing_set:
            duplicate_contacts_data.append(contact)
        elif not contact.email and not contact.linkedin_url:
            incomplete_contacts_data.append(contact)
        elif contact.uuid in removed_set:
            restored_contacts_data.append(contact)
        else:
            new_contacts_data.append(contact)

    new_contacts = ContactStatisticsBase(
        total=len(new_contacts_data),
        contacts=[
            ContactPreviewInfo(**new_contact_data.dict())
            for new_contact_data in new_contacts_data
        ],
    )

    restored_contacts = ContactStatisticsBase(
        total=len(restored_contacts_data),
        contacts=[
            ContactPreviewInfo(**remove_contact_data.dict())
            for remove_contact_data in restored_contacts_data
        ],
    )

    incomplete_contacts = ContactStatisticsBase(
        total=len(incomplete_contacts_data),
        contacts=[
            ContactPreviewInfo(**need_preview_contact_data.dict())
            for need_preview_contact_data in incomplete_contacts_data
        ],
    )

    duplicate_contacts = ContactStatisticsBase(
        total=len(duplicate_contacts_data),
        contacts=[
            ContactPreviewInfo(**cannot_add_contact_data.dict())
            for cannot_add_contact_data in duplicate_contacts_data
        ],
    )
    total = (
        len(new_contacts_data)
        + len(restored_contacts_data)
        + len(incomplete_contacts_data)
        + len(duplicate_contacts_data)
    )
    return GetPreviewContactResponse(
        new_contacts=new_contacts,
        restored_contacts=restored_contacts,
        incomplete_contacts=incomplete_contacts,
        duplicate_contacts=duplicate_contacts,
        total=total,
    )
