from sqlalchemy.sql import text
from sqlmodel import Session, col, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.users import UserBase
from app.models import TeamCompany
from app.models.team import PlanCode
from utils.extract_domain import extract_domain
from utils.mask_company_data import mask_company_data


def get_company_by_domain(
    db: Session, url: str, current_user: UserBase, listing_plan_code
):
    domain = extract_domain(url)
    query = """ SELECT c.*
              FROM companies c
              where c."domain" = :domain"""

    companies = db.execute(text(query), {"domain": domain}).all()

    corporate_numbers = [x["corporate_number"] for x in companies]

    corporate_numbers_downloaded = db.exec(
        select(TeamCompany.corporate_number)
        .where(TeamCompany.team_id == current_user.team_id)
        .where(col(TeamCompany.corporate_number).in_(corporate_numbers))
    ).all()

    data_companies = []

    for x in companies:
        d = {}
        for filed in x.keys():
            d[filed] = getattr(x, filed)
        data_companies.append(d)

    if listing_plan_code == PlanCode.UNLIMITED:
        return sorted(data_companies, key=lambda x: list(x.values()).count(None))[0]

    new_companies = mask_company_data(data_companies, corporate_numbers_downloaded)

    get_more_information = sorted(
        new_companies, key=lambda x: list(x.values()).count(None)
    )

    if not get_more_information:
        raise NotFoundException(detail="company.companyNotFound")

    return get_more_information[0]
