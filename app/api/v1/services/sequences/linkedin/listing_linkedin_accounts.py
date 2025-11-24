from sqlmodel import Session, func, select

from app.api.v1.schemas.sequence.linkedin_account import ListingAccountItem
from app.api.v1.schemas.users import UserBase
from app.models.sequence.linkedin_account import LinkedInAccount


def _get_linkedin_accounts_conditions(current_user: UserBase):
    """Returns the base conditions for querying active LinkedIn accounts for a team."""
    return [
        LinkedInAccount.team_id == current_user.team_id,
        LinkedInAccount.deleted_at.is_(None),
        LinkedInAccount.account_type == "LINKEDIN",
    ]


def listing_linkedin_accounts_service(
    db: Session, current_user: UserBase, page: int, per_page: int
):
    if page < 1:
        page = 1
    conditions = _get_linkedin_accounts_conditions(current_user)
    query = (
        select(LinkedInAccount)
        .where(*conditions)
        .order_by(LinkedInAccount.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    accounts = db.exec(query).all()
    data = [ListingAccountItem.from_orm(account) for account in accounts]
    return data


def count_linkedin_accounts_service(db: Session, current_user: UserBase):
    conditions = _get_linkedin_accounts_conditions(current_user)
    query = select(func.count(LinkedInAccount.id)).where(*conditions)
    total = db.exec(query).first()
    return total
