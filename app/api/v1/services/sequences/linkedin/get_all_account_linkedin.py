from sqlmodel import Session, select

from app.api.v1.schemas.sequence.linkedin_account import ListingAllAccountItem
from app.api.v1.schemas.users import UserBase
from app.models.sequence.linkedin_account import LinkedInAccount


def get_all_account_linkedin_service(db: Session, current_user: UserBase):
    condition = [
        LinkedInAccount.team_id == current_user.team_id,
        LinkedInAccount.account_type == "LINKEDIN",
        LinkedInAccount.deleted_at.is_(None),
    ]
    query = select(LinkedInAccount).where(*condition)
    accounts = db.exec(query).all()
    data = [
        ListingAllAccountItem(
            id=account.id,
            name=account.account_name,
            is_default=account.is_default,
        )
        for account in accounts
    ]
    return data
