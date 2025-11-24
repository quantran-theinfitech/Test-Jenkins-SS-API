from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.sequence.linkedin_account import ConfigAccountRequest
from app.api.v1.schemas.users import UserBase
from app.models.sequence.linkedin_account import FirstStepConfigEnum, LinkedInAccount


def update_linkedin_accounts_service(
    account_id: str, request: ConfigAccountRequest, db: Session, current_user: UserBase
):
    account = db.exec(
        select(LinkedInAccount).where(
            LinkedInAccount.account_id == account_id,
            LinkedInAccount.team_id == current_user.team_id,
            LinkedInAccount.deleted_at.is_(None),
        )
    ).first()
    if not account:
        raise NotFoundException("sequence.LinkedInAccountNotFound")

    try:
        # Check if first_step_config_type is provided in the request
        # then apply the corresponding logic
        if "first_step_config_type" in request.__fields_set__:
            if request.first_step_config_type == FirstStepConfigEnum.NEW_ACCOUNT:
                account.profile_views_per_day = 100
                account.connections_sent_per_day = 15
                account.connections_sent_per_week = 100
                account.messages_sent_per_day = 15
                account.messages_sent_per_week = 150
                account.request_interval_seconds = 100

            elif (
                request.first_step_config_type
                == FirstStepConfigEnum.PAID_OR_ACTIVE_ACCOUNT
            ):
                account.profile_views_per_day = 100
                account.connections_sent_per_day = 100
                account.connections_sent_per_week = 150
                account.messages_sent_per_day = 100
                account.messages_sent_per_week = 150
                account.request_interval_seconds = 100

            elif request.first_step_config_type == FirstStepConfigEnum.LATEST_SETTINGS:
                current_account = account
                # Get all accounts with the same team_id and not deleted
                accounts_same_team = db.exec(
                    select(LinkedInAccount).where(
                        LinkedInAccount.team_id == current_account.team_id,
                        LinkedInAccount.deleted_at.is_(None),
                        LinkedInAccount.account_id != account_id,
                    )
                ).all()

                if accounts_same_team:
                    # Find the account with the latest updated_at
                    latest_account_updated = max(
                        accounts_same_team,
                        key=lambda acc: acc.updated_at or datetime.min,
                    )
                    # Update fields from the latest account's settings
                    account.profile_views_per_day = (
                        latest_account_updated.profile_views_per_day
                    )
                    account.connections_sent_per_day = (
                        latest_account_updated.connections_sent_per_day
                    )
                    account.connections_sent_per_week = (
                        latest_account_updated.connections_sent_per_week
                    )
                    account.messages_sent_per_day = (
                        latest_account_updated.messages_sent_per_day
                    )
                    account.messages_sent_per_week = (
                        latest_account_updated.messages_sent_per_week
                    )
                    account.request_interval_seconds = (
                        latest_account_updated.request_interval_seconds
                    )

        # Handle default setting logic if request.is_default is True
        if hasattr(request, "is_default") and request.is_default:
            # Find previous default account (if any)
            previous_default = db.exec(
                select(LinkedInAccount).where(
                    LinkedInAccount.team_id == current_user.team_id,
                    LinkedInAccount.is_default.is_(True),
                    LinkedInAccount.deleted_at.is_(None),
                    LinkedInAccount.account_id != account_id,  # Exclude current account
                )
            ).first()

            # Unset previous default if it exists
            if previous_default:
                previous_default.is_default = False
                db.add(previous_default)

        # Update other fields from the request
        # if they are provided (excluding first_step_config_type)
        for key, value in request.dict(
            exclude_unset=True, exclude={"first_step_config_type"}
        ).items():
            setattr(account, key, value)

        # Update audit fields
        account.updated_at = datetime.now()
        account.updated_by = current_user.id

        db.add(account)
        db.commit()
        db.refresh(account)
        return account
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update LinkedIn account: {str(e)}"
        )
