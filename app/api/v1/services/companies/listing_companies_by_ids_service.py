from typing import List

from sqlmodel import Session, col, select

from app.api.base.exceptions import NotFoundException
from app.models import TeamCompany
from app.models.company import Company
from app.models.team import PlanCode
from utils.extract_domain import extract_full_domain_url

def listing_companies_by_ids(
    db: Session,
    corporate_numbers: List[str],
    current_user,
    listing_plan_code: PlanCode,
):
    companies = db.exec(
        select(Company).where(Company.corporate_number.in_(corporate_numbers))
    ).all()

    if not companies:
        raise NotFoundException(detail="company.companyNotFound")

    if listing_plan_code == PlanCode.UNLIMITED:
        data = []
        for company_row in companies:
            company = dict(company_row)
            company["downloaded_flag"] = True
            data.append(company)
        return data

    corporate_numbers_downloaded = db.exec(
        select(TeamCompany.corporate_number)
        .where(TeamCompany.team_id == current_user.team_id)
        .where(col(TeamCompany.corporate_number).in_(corporate_numbers))
    ).all()

    new_companies = mask_company_data(companies, corporate_numbers_downloaded)

    return new_companies


def mask_company_data(companies, corporate_numbers_downloaded):
    display_fields = [
        "id",
        "establish_at",
        "name",
        "address",
        "industry_code",
        "sub_industries_code",
        "listing_market_code",
        "president_name",
        "corporate_number",
        "postal_code",
        "favicon_url"
    ]

    sort_fields = [
        "employees_count",
        "revenue",
        "capital",
    ]

    processed_companies = []

    for row in companies:
        company = dict(row)
        domain_url = extract_full_domain_url(company["hp_url"])
        company["favicon_url"] = f"{domain_url}/favicon.ico"
        mask_fields = [
            x
            for x in company.keys()
            if x not in display_fields
            and x not in sort_fields
            and x != "id"
            and x != "corporate_number"
        ]
        available_fields = []

        if company["corporate_number"] not in corporate_numbers_downloaded:
            for field in mask_fields:
                if company[field] is not None:
                    available_fields.append(field)
                    company[field] = None
            company["downloaded_flag"] = False
        else:
            company["downloaded_flag"] = True

        company["available_fields"] = available_fields
        processed_companies.append(company)

    return processed_companies
