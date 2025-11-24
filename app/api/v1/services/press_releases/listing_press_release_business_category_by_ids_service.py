from typing import List

from sqlmodel import Session, select

from app.models.press_release_business_categories import PressReleaseBusinessCategory


def listing_press_release_business_category_by_ids(db: Session, ids: List[int]):
    return db.exec(
        select(PressReleaseBusinessCategory).where(
            PressReleaseBusinessCategory.id.in_(ids)
        )
    ).all()
