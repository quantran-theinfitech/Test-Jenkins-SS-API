from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, UploadFile
from fastapi.responses import PlainTextResponse
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.engagements import ListingContactsResponse
from app.api.v1.schemas.users import UserBase
from app.api.v1.services import contacts

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get("/", response_model=ListingContactsResponse)
def listing_contacts(
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    list = contacts.listing_contacts(db, current_user, page, per_page)
    total = contacts.listing_contacts_count(db, current_user)

    return ListingContactsResponse(page=page, per_page=per_page, total=total, data=list)


# @router.post("/", response_model=int)
# def create_contacts(
#     request: SaveContactRequest,
#     db: Session = Depends(get_session),
#     current_user: UserBase = Depends(get_current_user()),
# ):
#     return contacts.save_contact(request, db, current_user)


@router.post("/", response_model=int)
def create_contact_list(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):

    df = contacts.read_contact_list_csv(file)

    return contacts.save_contacts_from_csv(db, current_user, df)


@router.get("/download_template", response_class=PlainTextResponse)
def download_contact_list_template_csv(
    current_user: UserBase = Depends(get_current_user()),
):

    return contacts.download_contacts_template_csv()
