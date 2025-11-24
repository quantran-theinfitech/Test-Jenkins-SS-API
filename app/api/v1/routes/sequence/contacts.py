# flake8: noqa: E501

from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies.authentication import get_current_user
from app.api.v1.dependencies.services import get_cross_search_service
from app.api.v1.schemas.sequence.campaigns import (
    AddContactRequest,
    AddSequenceContactRequest,
    AddSequenceContactResponse,
    GetContactUuidsRequest,
    GetPreviewContactResponse,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.cross_search_service import CrossSearchService
from app.api.v1.services.sequences.contacts.add_list_to_sequence_contacts_service import (
    add_list_to_sequence_contacts_service,
)
from app.api.v1.services.sequences.contacts.create_sequence_contacts_service import (
    prepare_sequence_contacts,
    process_sequence_contacts,
)
from app.api.v1.services.sequences.contacts.get_sequence_contacts_service import (
    get_sequence_contact_service,
)

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.post("/{sequence_id}/contacts", response_model=int)
def create_sequence_contact(
    sequence_id: int,
    request: AddContactRequest,
):
    return 1


@router.post("/{sequence_id}/contacts/upload", response_model=int)
def upload_sequence_contacts_csv(
    sequence_id: int,
    request: AddContactRequest,
):
    return 1


# @router.get("/{sequence_id}/contacts", response_model=ListingContactResponse)
# def sequence_listing_contacts(
#     sequence_id: int,
#     per_page: Optional[int] = Query(default=5, ge=1),
#     page: Optional[int] = Query(default=1, ge=1),
#     keyword: Optional[str] = Query(default=None),
# ):
#     mock_data = generate_mock_listing_contact(page, per_page)
#     return mock_data


# @router.get(
#     "/{sequence_id}/contacts/{contact_id}", response_model=ContactDetailResponse
# )
# def get_sequence_contact_detail(
#     sequence_id: int,
#     contact_id: int,
# ):
#     mock_data = generate_mock_contact_detail(sequence_id, contact_id)
#     return mock_data


@router.post(
    "/{sequence_campaign_id}/preview_contacts", response_model=GetPreviewContactResponse
)
def get_preview_contacts(
    sequence_campaign_id: int,
    contact_uuids: GetContactUuidsRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return get_sequence_contact_service(
        sequence_campaign_id, contact_uuids, db, current_user
    )


# @router.post("/contacts", response_model=AddSequenceContactResponse)
# def create_sequence_contacts(
#     request: AddSequenceContactRequest,
#     background_task: BackgroundTasks,
#     current_user: UserBase = Depends(get_current_user()),
#     cross_search_service: CrossSearchService = Depends(get_cross_search_service),
# ):
#     background_task.add_task(
#         create_sequence_contact_service, request, current_user, cross_search_service
#     )
#     return {"success": True}


@router.post("/contacts", response_model=AddSequenceContactResponse)
async def create_sequence_contacts(
    request: AddSequenceContactRequest,
    background_task: BackgroundTasks,
    current_user: UserBase = Depends(get_current_user()),
    # cross_search_service: CrossSearchService = Depends(get_cross_search_service),
):
    # phần này chạy sync/async trong request => có thể raise lỗi
    data = await prepare_sequence_contacts(request, current_user)

    # Sau khi pass hết validate thì mới add background
    background_task.add_task(process_sequence_contacts, data)

    return {"success": True}


@router.post("/{sequence_campaign_id}/contacts/add_list", response_model=int)
def add_list_sequence_contacts(
    sequence_campaign_id: int,
    list_id: int,
    background_task: BackgroundTasks,
    is_include_incompleted_contacts: Optional[bool] = Query(default=None),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    background_task.add_task(
        add_list_to_sequence_contacts_service,
        sequence_campaign_id,
        list_id,
        db,
        current_user,
        is_include_incompleted_contacts
    )
    return sequence_campaign_id
