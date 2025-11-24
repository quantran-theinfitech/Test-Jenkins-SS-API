from sqlmodel import Session, select

from app.api.v1.schemas.users import UserBase
from app.models.company_bookmark import CompanyBookmark


def un_bookmark_company(db: Session, company_id: int, current_user: UserBase):
    bookmark = db.exec(
        select(CompanyBookmark)
        .where(CompanyBookmark.company_id == company_id)
        .where(CompanyBookmark.user_id == current_user.id)
    ).one()
    db.delete(bookmark)
    db.commit()
    return bookmark
