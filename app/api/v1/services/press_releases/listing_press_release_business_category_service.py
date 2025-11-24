from sqlalchemy import func
from sqlmodel import Session, select

from app.api.v1.schemas.press_releases import ListingPRbusinessCategoryQueryParams
from app.models.press_release_business_categories import PressReleaseBusinessCategory


def listing_press_release_business_category(
    db: Session, request: ListingPRbusinessCategoryQueryParams
):
    categories_query = select(PressReleaseBusinessCategory)

    total_categories_query = select(func.count(PressReleaseBusinessCategory.id))

    if request.keyword:
        categories_query = categories_query.where(
            PressReleaseBusinessCategory.name.ilike(f"%{request.keyword}%")
        )
        total_categories_query = total_categories_query.where(
            PressReleaseBusinessCategory.name.ilike(f"%{request.keyword}%")
        )

    categories_query = (
        categories_query.offset((request.page - 1) * request.per_page)
        .limit(request.per_page)
        .order_by(PressReleaseBusinessCategory.id.desc())
    )
    categories = db.exec(categories_query).all()
    total = db.exec(total_categories_query).first()
    return categories, total
