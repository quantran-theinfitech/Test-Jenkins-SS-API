# flake8: noqa: E501
from datetime import datetime

from sqlalchemy import and_
from sqlmodel import Session, select, text

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.companies import GetCompanyActivitesRequest
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.press_release_service import PressReleaseService
from app.constant.constants import TECHNOLOGY_LIMIT
from app.models import Company, TeamCompany
from app.models.company_service import CompanyService
from app.models.event import Event
from app.models.person import Person
from app.models.team import PlanCode
from app.models.technology import Technology
from app.models.technology_category import TechnologyCategory
from utils.extract_domain import extract_full_domain_url


def get_company_detail(
    db: Session, corporate_number: str, current_user: UserBase, listing_plan_code
):
    try:
        company_downloaded = db.exec(
            select(Company, TeamCompany.status_code, TeamCompany.tags)
            .join(
                TeamCompany,
                Company.corporate_number == TeamCompany.corporate_number,
                isouter=True,
            )
            .where(
                and_(
                    TeamCompany.corporate_number == corporate_number,
                    TeamCompany.team_id == current_user.team_id,
                )
            )
        ).first()

        if not company_downloaded:
            company = db.exec(
                select(Company, TeamCompany.status_code, TeamCompany.tags)
                .join(
                    TeamCompany,
                    Company.corporate_number == TeamCompany.corporate_number,
                    isouter=True,
                )
                .where(Company.corporate_number == corporate_number)
            ).first()
        else:
            company = company_downloaded

        if company:
            company_detail = {
                k: v for k, v in company[0].__dict__.items() if not k.startswith("_")
            }

            company_detail.update(
                {
                    "status_code": company[1],
                }
                if company[1]
                else {}
            )

            company_tags = db.exec(
                select(TeamCompany.tags).where(
                    and_(
                        TeamCompany.corporate_number == corporate_number,
                        TeamCompany.team_id == current_user.team_id,
                    )
                )
            ).first()

            company_detail["tags"] = company_tags if company_tags else []

            # Thêm favicon_url cho mọi trường hợp
            domain_url = extract_full_domain_url(company_detail.get("hp_url"))
            if domain_url:
                company_detail["favicon_url"] = f"{domain_url}/favicon.ico"
            else:
                company_detail["favicon_url"] = None

            if listing_plan_code == PlanCode.UNLIMITED:
                company_detail["downloaded_flag"] = True
                return company_detail

            company_downloaded = db.exec(
                select(TeamCompany).where(
                    and_(
                        TeamCompany.corporate_number == corporate_number,
                        TeamCompany.team_id == current_user.team_id,
                    )
                )
            ).first()

            if not company_downloaded:
                return mask_company_data(company_detail)

            company_detail["downloaded_flag"] = True
            return company_detail
        else:
            raise NotFoundException("company.companyNotFound")
    except Exception as e:
        print("_______ error get_company_detail _______", str(e))
        raise e


def mask_company_data(company):
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
        "favicon_url",
    ]

    mask_fields = [
        x
        for x in company.keys()
        if x not in display_fields and x != "id" and x != "corporate_number"
    ]
    available_fields = []
    code_lists = [
        "tool_codes",
        "press_release_media_codes",
        "recruit_media_codes",
        "business_model_codes",
    ]
    for field in mask_fields:
        if (field not in code_lists and company.get(field) is not None) or (
            field in code_lists
            and company.get(field) is not None
            and len(company.get(field)) > 0
        ):
            available_fields.append(field)
            company[field] = None
    company["downloaded_flag"] = False
    company["available_fields"] = available_fields

    return company


def get_company_activities(
    db: Session,
    request: GetCompanyActivitesRequest,
    current_user: UserBase,
    listing_plan_code: PlanCode,
):
    try:
        company_downloaded = None
        if listing_plan_code != PlanCode.UNLIMITED:
            company_downloaded = db.exec(
                select(TeamCompany).where(
                    and_(
                        TeamCompany.corporate_number == request.corporate_number,
                        TeamCompany.team_id == current_user.team_id,
                    )
                )
            ).first()

        if company_downloaded is None:
            request.per_page = 5
            request.page = 1

        query = """SELECT *
                FROM (
                    SELECT pr.title, pr.content, pr.media_code, 'PRESS_RELEASE' AS activity_type, pr.posted_at as posted_at, pr.source_article_url as source_url
                    FROM press_releases pr
                    WHERE pr.corporate_number = :corporate_number
                    UNION
                    SELECT r.title, r.content, r.media_code, 'RECRUITMENT' AS activity_type, r.start_at as posted_at, r.source_recruit_url as source_url
                    FROM recruits r
                    WHERE r.corporate_number = :corporate_number
                    UNION
                    SELECT e.name as title, e.content, e.media_code, 'EVENT' AS activity_type, e.start_time as posted_at, e.source_event_url as source_url
                    FROM events e
                    WHERE e.corporate_number = :corporate_number
                ) tmp
                ORDER BY tmp.posted_at DESC NULLS LAST
                LIMIT :limit OFFSET :offset
                """
        company_activities = (
            db.execute(
                text(query),
                {
                    "corporate_number": request.corporate_number,
                    "limit": request.per_page,
                    "offset": (request.page - 1) * request.per_page,
                },
            )
            .mappings()
            .all()
        )

        for activity in company_activities:
            if isinstance(activity["posted_at"], str):
                activity["posted_at"] = datetime.strptime(
                    activity["posted_at"], "%Y-%m-%dT%H:%M:%S.%f"
                )
            elif activity["posted_at"] is None:
                pass

        return company_activities
    except Exception as e:
        print("_______ error get_company_activities _______", str(e))
        raise e


def get_company_technologies(
    db: Session,
    corporate_number: str,
    is_limit: bool,
):
    try:
        result = db.exec(
            select(Technology, TechnologyCategory.name.label("category_name"))
            .join(
                TechnologyCategory,
                Technology.technology_category_id == TechnologyCategory.id,
            )
            .where(
                Technology.corporate_number == corporate_number,
            )
        ).all()

        category_mapping = {}

        for technology, category_name in result:
            if not category_mapping.get(category_name):
                category_mapping[category_name] = {
                    "category_name": category_name,
                    "technology": [],
                }
            category_mapping[category_name]["technology"].append(
                {
                    "name": technology.name,
                    "icon": technology.icon,
                    "website": technology.website,
                }
            )

        categories = list(category_mapping.values())
        if is_limit:
            if len(categories) >= TECHNOLOGY_LIMIT:
                return [
                    {
                        "category_name": cat["category_name"],
                        "technology": (
                            [cat["technology"][0]] if cat["technology"] else []
                        ),
                    }
                    for cat in categories[:TECHNOLOGY_LIMIT]
                ]
            else:
                result = []
                total_technologies_result = 0
                total_technologies_categories = sum(
                    len(cat["technology"]) for cat in categories
                )
                loop_while = 0

                category_map = {cat["category_name"]: [] for cat in categories}

                while (
                    total_technologies_result < TECHNOLOGY_LIMIT
                    and total_technologies_result < total_technologies_categories
                ):
                    for cat in categories:
                        tech_list = cat["technology"]
                        if loop_while < len(tech_list):
                            category_name = cat["category_name"]
                            category_map[category_name].append(tech_list[loop_while])
                            total_technologies_result += 1

                            if total_technologies_result >= TECHNOLOGY_LIMIT:
                                break
                    loop_while += 1

                result = [
                    {"category_name": name, "technology": techs}
                    for name, techs in category_map.items()
                    if techs
                ]

                return result

        return categories
    except Exception as e:
        print("_______ error get_company_technologies _______", str(e))
        raise e
