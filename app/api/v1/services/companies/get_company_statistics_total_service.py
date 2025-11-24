from sqlmodel import Session, and_, func, or_

from app.api.v1.schemas.companies import (
    CompanyDetailStatisticData,
    CompanyDetailStatisticTotalResponse,
)
from app.api.v1.schemas.users import UserBase
from app.models.company_investor_relations import CompanyInvestorRelations
from app.models.company_service import CompanyService
from app.models.event import Event
from app.models.person import Person
from app.models.press_release import PressRelease
from app.models.recruit import Recruit
from app.models.technology import Technology


def get_company_statistics_total(
    db: Session,
    current_user: UserBase,
    corporate_number: str,
) -> CompanyDetailStatisticTotalResponse:
    recruits_total = (
        db.query(func.count(Recruit.corporate_number))
        .filter(Recruit.corporate_number == corporate_number)
        .scalar()
    )
    press_releases_total = (
        db.query(func.count(PressRelease.corporate_number))
        .filter(PressRelease.corporate_number == corporate_number)
        .scalar()
    )
    events_total = (
        db.query(func.count(Event.corporate_number))
        .filter(Event.corporate_number == corporate_number)
        .scalar()
    )
    employees_total = (
        db.query(func.count(Person.uuid))
        .filter(Person.corporate_number.op("@>")([corporate_number]))
        .scalar()
    )
    services_total = (
        db.query(func.count(CompanyService.id))
        .filter(
            CompanyService.corporate_number.op("@>")([corporate_number]),
            or_(
                func.coalesce(func.nullif(func.trim(CompanyService.name), ""), "")
                != "",
                func.coalesce(
                    func.nullif(func.trim(CompanyService.description), ""), ""
                )
                != "",
                func.coalesce(func.nullif(func.trim(CompanyService.title), ""), "")
                != "",
                and_(
                    CompanyService.name_tags.isnot(None),
                    func.cardinality(CompanyService.name_tags) > 0,
                ),
            ),
        )
        .scalar()
    )
    technologies_total = (
        db.query(func.count(Technology.corporate_number))
        .filter(Technology.corporate_number == corporate_number)
        .scalar()
    )
    investor_relations_total = (
        db.query(func.count(CompanyInvestorRelations.corporate_number))
        .filter(CompanyInvestorRelations.corporate_number == corporate_number)
        .scalar()
    )
    return CompanyDetailStatisticTotalResponse(
        data=CompanyDetailStatisticData(
            recruits_total=recruits_total if recruits_total else 0,
            press_releases_total=press_releases_total if press_releases_total else 0,
            events_total=events_total if events_total else 0,
            employees_total=employees_total if employees_total else 0,
            services_total=services_total if services_total else 0,
            technologies_total=technologies_total if technologies_total else 0,
            investor_relations_total=investor_relations_total
            if investor_relations_total
            else 0,
        )
    )
