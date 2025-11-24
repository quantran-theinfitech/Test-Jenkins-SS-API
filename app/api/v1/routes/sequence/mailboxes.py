from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.sequence.mail_aliases import ListingMailAliases
from app.api.v1.schemas.sequence.mailboxes import (
    AddMailboxRequest,
    ListSimpleMailSenderResponse,
    MailboxBase,
    MailboxConfigStepStatusResponse,
    MailBoxList,
    SimpleMailSenderResponse,
    UpdateMailboxRequest,
    VerifyDomainMailboxResponse,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.mailboxes import (
    count_listing_mailboxes_service,
    create_mailbox_service,
    delete_mailbox_service,
    get_config_step_status_service,
    get_detail_mailbox_service,
    get_mailbox_limit_service,
    get_mailbox_verify_status,
    listing_mail_alias_service,
    listing_mailboxes_service,
    refresh_mail_alias_service,
    update_mailbox_service,
)
from app.api.v1.services.sequences.mailboxes.get_filter_mail_sender_service import (
    get_filter_mail_sender_service,
)

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.post("/mailbox", status_code=201, response_model=MailboxBase)
def create_mailbox(
    request: AddMailboxRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return create_mailbox_service(db, current_user, request)


@router.get("/mailbox/limit", response_model=bool)
def get_mailbox_limit(
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return get_mailbox_limit_service(db, current_user)


@router.get(
    "/mailbox/{mailbox_id}/verify_domain", response_model=VerifyDomainMailboxResponse
)
def verify_domain_mailbox(
    mailbox_id: int,
    db: Session = Depends(get_session),
):
    data = get_mailbox_verify_status(mailbox_id, db)
    return data


@router.get("/mailboxes", response_model=MailBoxList)
def get_listing_mailboxes(
    per_page: int = Query(default=0, ge=0),
    page: int = Query(default=1, ge=1),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    data = listing_mailboxes_service(db, current_user, page, per_page)
    total, limit = count_listing_mailboxes_service(db, current_user)
    return MailBoxList(
        page=page, per_page=per_page, total=total, data=data, limit=limit
    )


@router.get("/mailbox/{mailbox_id}", response_model=MailboxBase)
def get_detail_mailbox(
    mailbox_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return get_detail_mailbox_service(mailbox_id, db, current_user)


@router.put("/mailboxes/{mailbox_id}", response_model=MailboxBase)
def update_mailbox(
    mailbox_id: int,
    request: UpdateMailboxRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return update_mailbox_service(mailbox_id, request, db, current_user)


@router.delete("/mailboxes/{mailbox_id}", status_code=200)
def delete_mailbox(
    mailbox_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return delete_mailbox_service(mailbox_id, db, current_user)


@router.post("/mailbox/{mailbox_id}/aliases/refresh", response_model=ListingMailAliases)
def refresh_mail_alias(
    mailbox_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return refresh_mail_alias_service(mailbox_id, db)


@router.get("/mailbox/{mailbox_id}/aliases", response_model=ListingMailAliases)
def get_mail_aliases(
    mailbox_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return listing_mail_alias_service(mailbox_id, db)


@router.get(
    "/mailbox/{mailbox_id}/config-status",
    response_model=MailboxConfigStepStatusResponse,
)
def get_config_step_status(
    mailbox_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return get_config_step_status_service(mailbox_id, db)


@router.get(
    "/{sequence_campaign_id}/mail_senders",
    response_model=Optional[ListSimpleMailSenderResponse],
)
def get_filter_mail_sender(
    sequence_campaign_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    data = get_filter_mail_sender_service(db, current_user, sequence_campaign_id)
    return ListSimpleMailSenderResponse(data=data)
