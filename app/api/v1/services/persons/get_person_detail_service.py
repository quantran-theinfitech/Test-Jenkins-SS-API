from sqlalchemy import and_
from sqlmodel import Session, select

from app.api.v1.schemas.users import UserBase
from app.models import TeamPerson
from app.models.team import PlanCode

from .get_person_by_uuid import get_person_by_uuid


def get_person_detail(
    db: Session, person_uuid: str, current_user: UserBase, listing_plan_code
):
    person = get_person_by_uuid(db, person_uuid)

    person_detail = dict(person)

    if listing_plan_code == PlanCode.UNLIMITED:
        person_detail["downloaded_flag"] = True
        return person_detail

    person_downloaded = db.exec(
        select(TeamPerson).where(
            and_(
                TeamPerson.person_uuid == person_uuid,
                TeamPerson.team_id == current_user.team_id,
            )
        )
    ).first()

    if not person_downloaded:
        return mask_person_data(person_detail)

    person_detail["downloaded_flag"] = True
    return person_detail


def mask_person_data(person):
    if person["name"]:
        person["name"] = person["name"][: len(person["name"]) // 2]

    display_fields = [
        "id",
        "uuid",
        "name",
        "address",
        "company_name",
        "role_name",
        "corporate_number",
    ]

    mask_fields = [x for x in person.keys() if x not in display_fields and x != "id"]
    available_fields = []
    for field in mask_fields:
        if person[field]:
            available_fields.append(field)
            person[field] = None
    person["downloaded_flag"] = False

    return person
