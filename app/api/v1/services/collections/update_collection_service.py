import datetime

from sqlmodel import Session, select

from app.api.base.exceptions import BadRequestException, NotFoundException
from app.api.v1.schemas.collections import UpdateCollectionRequest
from app.models import CompanyCollection
from app.models.user import User


def update_collection(
    db: Session,
    collection_id: int,
    current_user: User,
    request: UpdateCollectionRequest,
):
    company_collection = db.exec(
        select(CompanyCollection)
        .where(CompanyCollection.team_id == current_user.team_id)
        .where(CompanyCollection.id == collection_id)
    ).first()
    if not company_collection:
        raise NotFoundException(detail="company.notFound")
    if request.name:
        existing_collection = db.exec(
            select(CompanyCollection)
            .where(CompanyCollection.team_id == current_user.team_id)
            .where(CompanyCollection.name == request.name)
            .where(CompanyCollection.id != collection_id)
        ).first()
        if existing_collection:
            raise BadRequestException(detail="common.duplicateName")
    for attr, value in request.dict(exclude_unset=True).items():
        setattr(company_collection, attr, value)
    company_collection.updated_by = current_user.id
    company_collection.updated_at = datetime.datetime.now()
    db.add(company_collection)
    db.commit()
    db.refresh(company_collection)
    return company_collection
