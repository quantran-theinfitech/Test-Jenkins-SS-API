import datetime

from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.models import CompanyCollection
from app.models.user import User


def delete_collection(db: Session, collection_id: int, current_user: User):
    company_collection = db.exec(
        select(CompanyCollection)
        .where(CompanyCollection.team_id == current_user.team_id)
        .where(CompanyCollection.id == collection_id)
    ).first()
    if not company_collection:
        raise NotFoundException(detail="company.notFound")
    company_collection.deleted_by = current_user.id
    company_collection.deleted_at = datetime.datetime.now()
    db.add(company_collection)
    db.commit()
    db.refresh(company_collection)
    return company_collection.id
