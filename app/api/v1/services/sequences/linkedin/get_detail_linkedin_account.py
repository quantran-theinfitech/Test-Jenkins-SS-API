from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.sequence.linkedin_account import (
    LinkedInAccountBase,
    LinkedinConfigStepStatusResponse,
)
from app.api.v1.schemas.users import UserBase
from app.models.sequence.linkedin_account import LinkedInAccount


def get_config_status_service(
    account_id: str,
    db: Session,
):
    condition = [
        LinkedInAccount.account_id == account_id,
        LinkedInAccount.deleted_at.is_(None),
    ]

    query = select(LinkedInAccount).where(*condition)
    account = db.exec(query).first()
    if not account:
        raise NotFoundException("sequence.LinkedInAccountNotFound")
    is_message_limit_done = (
        account.messages_sent_per_day is not None
        and account.messages_sent_per_week is not None
    )
    is_connect_limit_done = (
        account.connections_sent_per_day is not None
        and account.connections_sent_per_week is not None
    )
    is_view_profile_limit_done = account.profile_views_per_day is not None
    return LinkedinConfigStepStatusResponse(
        is_message_limit_done=is_message_limit_done,
        is_connect_limit_done=is_connect_limit_done,
        is_view_profile_limit_done=is_view_profile_limit_done,
        is_request_interval_done=True,
    )


def get_detail_linkedin_account_service(
    account_id: str, db: Session, current_user: UserBase
):
    condition = [
        LinkedInAccount.account_id == account_id,
        LinkedInAccount.deleted_at.is_(None),
    ]

    query = select(LinkedInAccount).where(*condition)
    account = db.exec(query).first()
    if not account:
        raise NotFoundException("sequence.LinkedInAccountNotFound")
    is_current_user = current_user.id == account.user_id
    if not account:
        raise NotFoundException(detail="sequence.LinkedInAccountNotFound")
    return LinkedInAccountBase(
        **account.dict(),
        config_step_status=get_config_status_service(account_id, db),
        is_current_user=is_current_user
    )
