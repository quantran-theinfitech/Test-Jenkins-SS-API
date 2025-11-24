from sqlmodel import Session, select

from app.api.v1.schemas.users import UserBase
from app.models.company_bookmark import CompanyBookmark


def bookmark_company(db: Session, company_id: int, current_user: UserBase):
    bookmark = db.exec(
        select(CompanyBookmark)
        .where(CompanyBookmark.company_id == company_id)
        .where(CompanyBookmark.user_id == current_user.id)
    ).first()
    if not bookmark:
        bookmark = CompanyBookmark(
            user_id=current_user.id,
            company_id=company_id,
        )
        db.add(bookmark)
        db.commit()
        return bookmark
