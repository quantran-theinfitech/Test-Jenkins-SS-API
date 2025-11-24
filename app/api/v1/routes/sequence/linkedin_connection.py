from datetime import datetime
from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session, select

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.base.exceptions import BadRequestException
from app.api.v1.dependencies.authentication import get_current_user
from app.api.v1.schemas.sequence.linkedin_account import (
    ConfigAccountRequest,
    ConnectType,
    HostedAuthCallback,
    HostedAuthUrlRequest,
    HostedAuthUrlResponse,
    LinkedInAccountBase,
    ListingAccountResponse,
    ListingAllAccountResponse,
    ListLinkedinSenderResponse,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.linkedin import get_all_account_linkedin_service
from app.api.v1.services.sequences.linkedin.get_detail_linkedin_account import (
    get_detail_linkedin_account_service,
)
from app.api.v1.services.sequences.linkedin.get_filter_linkedin_account_service import (
    get_filter_linkedin_account_service,
)
from app.api.v1.services.sequences.linkedin.handle_account_callback import (
    handle_account_callback_service,
)
from app.api.v1.services.sequences.linkedin.linkedin_webhook_service import (
    linkedin_webhook_service,
)
from app.api.v1.services.sequences.linkedin.listing_linkedin_accounts import (
    count_linkedin_accounts_service,
    listing_linkedin_accounts_service,
)
from app.api.v1.services.sequences.linkedin.update_linkedin_accounts import (
    update_linkedin_accounts_service,
)
from app.config import settings
from app.models.sequence.linkedin_account import LinkedInAccount
from app.models.team_credit import ServiceCode
from utils.credit_utils import is_enough_credit
from utils.optimize_time import format_expires_on

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.post("/linkedin/url", response_model=HostedAuthUrlResponse)
def generate_host_link(
    request: HostedAuthUrlRequest,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    if request.type == ConnectType.create and not is_enough_credit(
        db, current_user.team_id, 1, ServiceCode.LINKEDIN_CONNECT
    ):
        raise BadRequestException(detail="linkedinConnect.notEnoughCredit")

    expires_val = format_expires_on(request.expiresOn) if request.expiresOn else None

    account_id = request.account_id

    payload = {
        "type": request.type.value,  # "CREATE" hoặc "RECONNECT"
        "providers": ["LINKEDIN"],  # chuẩn giá trị
        "api_url": f"https://{settings.UNIPILE_DSN}",
        **({"expiresOn": expires_val} if expires_val else {}),
        "notify_url": settings.UNIPILE_NOTIFY_URL,
        "success_redirect_url": (
            f"{settings.UNIPILE_SUCCESS_URL}?account_id={account_id}"
            "&is_default_config=true"
        ),
        "name": str(current_user.id),
    }
    if request.type == ConnectType.reconnect:
        payload["reconnect_account"] = account_id

    headers = {
        "X-API-KEY": settings.UNIPILE_APIKEY,
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"https://{settings.UNIPILE_DSN}/api/v1/hosted/accounts/link",
        json=payload,
        headers=headers,
    )
    return response.json()


@router.post("/linkedin/callback")
def handle_callback_url(
    data: HostedAuthCallback,
    db: Session = Depends(get_session),
):
    handle_account_callback_service(data, db)
    return {"message": "received"}


@router.delete("/linkedin/delete/{linkedin_account_id}", status_code=200)
def delete_linkedin_account(
    linkedin_account_id: str,
    current_user: UserBase = Depends(get_current_user()),
    db: Session = Depends(get_session),
):
    account = db.exec(
        select(LinkedInAccount).where(
            LinkedInAccount.account_id == linkedin_account_id,
            LinkedInAccount.deleted_at.is_(None),
        )
    ).first()
    if not account:
        raise HTTPException(status_code=400, detail="sequence.AccountNotFound")

    # Gọi API Unipile để xóa
    headers = {
        "X-API-KEY": settings.UNIPILE_APIKEY,
        "Content-Type": "application/json",
    }
    response = requests.get(
        f"https://{settings.UNIPILE_DSN}/api/v1/accounts/{account.account_id}",
        headers=headers,
    )
    delete_response = None
    if response.status_code == 200:
        delete_response = requests.delete(
            f"https://{settings.UNIPILE_DSN}/api/v1/accounts/{account.account_id}",
            headers=headers,
        )
    if (
        delete_response and delete_response.status_code in (200, 204)
    ) or response.status_code == 404:
        account.deleted_at = datetime.now()
        account.deleted_by = current_user.id
        account.is_default = False
        db.add(account)
        db.flush()
        first_account = db.exec(
            select(LinkedInAccount)
            .where(
                LinkedInAccount.team_id == current_user.team_id,
                LinkedInAccount.deleted_at.is_(None),
                LinkedInAccount.account_type == "LINKEDIN",
            )
            .order_by(LinkedInAccount.id.asc())
        ).first()
        if first_account:
            first_account.is_default = True
            db.add(first_account)
        db.commit()
        return {"message": "Unlink linkedin successfully"}
    else:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Failed to unlink from Unipile: {response.status_code} - "
                f"{response.text}"
            ),
        )


@router.get("/linkedin", response_model=Optional[ListingAccountResponse])
def listing_linkedin_accounts(
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
    page: int = Query(default=1),
    per_page: int = Query(default=5),
):
    data = listing_linkedin_accounts_service(db, current_user, page, per_page)
    total = count_linkedin_accounts_service(db, current_user)
    return ListingAccountResponse(page=page, per_page=per_page, total=total, data=data)


@router.get(
    "/linkedin_activities/account", response_model=Optional[ListingAllAccountResponse]
)
def get_all_account_linkedin(
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    data = get_all_account_linkedin_service(db, current_user)
    return ListingAllAccountResponse(data=data)


@router.get(
    "/{sequence_campaign_id}/linkedin_activities/linkedin_senders",
    response_model=Optional[ListLinkedinSenderResponse],
)
def get_filter_linkedin_account(
    sequence_campaign_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    data = get_filter_linkedin_account_service(db, current_user, sequence_campaign_id)
    return ListLinkedinSenderResponse(data=data)


@router.put("/linkedin/{account_id}")
def update_linkedin_accounts(
    account_id: str,
    request: ConfigAccountRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return update_linkedin_accounts_service(account_id, request, db, current_user)


@router.get("/linkedin/{account_id}", response_model=Optional[LinkedInAccountBase])
def get_detail_linkedin_account(
    account_id: str,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return get_detail_linkedin_account_service(account_id, db, current_user)


@router.post("/linkedin/webhook")
async def linkedin_webhook(
    request: Request,
    db: Session = Depends(get_session),
):
    return await linkedin_webhook_service(request, db)
