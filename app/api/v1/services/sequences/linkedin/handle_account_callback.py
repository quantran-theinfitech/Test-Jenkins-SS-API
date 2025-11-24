# flake8: noqa
from datetime import datetime

import requests
from sqlmodel import Session, select

from app.api.base.exceptions import BadRequestException, NotFoundException
from app.api.v1.schemas.sequence.linkedin_account import HostedAuthCallback
from app.config import settings
from app.db import engine
from app.models.sequence.linkedin_account import LinkedInAccount, LinkedInAccountStatus
from app.models.team_credit import ServiceCode
from app.models.user import User
from utils.credit_utils import consume_credit


def retrieve_an_account(account_id: str):
    headers = {
        "X-API-KEY": settings.UNIPILE_APIKEY,
        "Content-Type": "application/json",
    }
    return requests.get(
        f"https://{settings.UNIPILE_DSN}/api/v1/accounts/{account_id}", headers=headers
    )


def handle_account_callback_service(data: HostedAuthCallback, db: Session):
    # Lấy thông tin account của tài khoản Linkedin -> trích xuất account_name, public_identifier
    profile_raw = retrieve_an_account(data.account_id)
    if not profile_raw:
        raise NotFoundException("sequence.LinkedinAccountNotFound")
    profile = profile_raw.json()  # profile kiểu dict khi dùng .json()
    # Lấy tên tài khoản linkedin
    account_name = profile.get("connection_params").get("im").get("username")
    # Xác định địa chỉ tài khoản linkedin
    public_identifier = (
        profile.get("connection_params").get("im").get("publicIdentifier")
    )
    # Xác định account_type
    account_type = profile.get("type")
    # Xác định user nào của Salessmart connect linkedin
    user = db.exec(select(User).where(User.id == int(data.name))).first()
    condition = [
        LinkedInAccount.deleted_at.is_(None),
        LinkedInAccount.account_type == "LINKEDIN",
        LinkedInAccount.team_id == user.team_id,
    ]
    exist_account = db.exec(select(LinkedInAccount).where(*condition)).all()

    condition.append(LinkedInAccount.public_identifier == public_identifier)
    linkedin_account = db.exec(select(LinkedInAccount).where(*condition)).first()

    if linkedin_account:
        if data.status == LinkedInAccountStatus.CREATION_SUCCESS:
            headers = {
                "X-API-KEY": settings.UNIPILE_APIKEY,
                "Content-Type": "application/json",
            }
            delete_response = requests.delete(
                f"https://{settings.UNIPILE_DSN}/api/v1/accounts/{data.account_id}",
                headers=headers,
            )
        else:
            linkedin_account.status = data.status
            linkedin_account.updated_at = datetime.now()
            db.add(linkedin_account)
    else:
        new_account = LinkedInAccount(
            user_id=int(data.name),
            created_by=int(data.name),
            status=data.status,
            account_id=data.account_id,
            account_name=account_name,
            team_id=user.team_id,
            public_identifier=public_identifier,
            account_type=account_type,
            is_default=False if exist_account else True,
            profile_views_per_day=100,
            connections_sent_per_day=15,
            connections_sent_per_week=100,
            messages_sent_per_day=15,
            messages_sent_per_week=150,
            request_interval_seconds=100,
        )
        db.add(new_account)
        with db.begin(nested=True):
            consume_credit(
                db,
                user.team_id,
                1,
                ServiceCode.LINKEDIN_CONNECT,
            )
    db.commit()
    return {"message": "success"}
