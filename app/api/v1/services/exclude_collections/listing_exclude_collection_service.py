from typing import List, Optional

from sqlalchemy import distinct, func
from sqlmodel import Session, col, desc, select

from app.api.v1.schemas.exclude_collections import ListingCompanyExcludeCollectionItem
from app.models.company_exclude_collection import CompanyExcludeCollection
from app.models.company_exclude_collection_item import CompanyExcludeCollectionItem
from app.models.user import User


def listing_all_exclude_collections(
    db: Session,
    current_user: User,
    keyword: Optional[str] = None,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
) -> List[ListingCompanyExcludeCollectionItem]:
    query = (
        select(
            CompanyExcludeCollection.id,
            CompanyExcludeCollection.team_id,
            CompanyExcludeCollection.name,
            CompanyExcludeCollection.type_code,
            CompanyExcludeCollection.identification_rate,
            CompanyExcludeCollection.csv_path,
            CompanyExcludeCollection.created_at,
            CompanyExcludeCollection.created_by,
            func.count(distinct(CompanyExcludeCollectionItem.corporate_number)).label(
                "companies_count"
            ),
        )
        .join(
            CompanyExcludeCollectionItem,
            CompanyExcludeCollectionItem.collection_id == CompanyExcludeCollection.id,
            isouter=True,
        )
        .where(CompanyExcludeCollection.team_id == current_user.team_id)
    )
    query = query.order_by(desc(CompanyExcludeCollection.id)).group_by(
        CompanyExcludeCollection.id
    )

    if page is not None and per_page is not None:
        query = query.offset((page - 1) * per_page)
        query = query.limit(per_page)

    if keyword is not None:
        query = query.where(col(CompanyExcludeCollection.name).ilike(f"%{keyword}%"))

    company_exclude_collections = db.execute(query).all()
    return company_exclude_collections


def count_listing_all_exclude_collections(
    db: Session, current_user: User, keyword: Optional[str] = None
):
    total_query = select(CompanyExcludeCollection).where(
        CompanyExcludeCollection.team_id == current_user.team_id
    )
    if keyword is not None:
        total_query = total_query.where(
            col(CompanyExcludeCollection.name).ilike(f"%{keyword}%")
        )
    total = (
        db.execute(
            total_query.with_only_columns(
                func.count(distinct(CompanyExcludeCollection.id))
            )
        ).scalar()
        or 0
    )

    return total
