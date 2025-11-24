from typing import Optional

from sqlmodel import Session, and_, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.hubspot_connections import (
    HubspotManualPullLogsDetail,
    HubspotManualPullLogsDetailResponse,
)
from app.api.v1.schemas.users import UserBase
from app.models import (
    Company,
    HubspotCompanyMultiplePullHistories,
    HubspotCompanyPullHistories,
    HubspotIntergrations,
    TeamCompany,
)
from app.models.integration.hubspot.hubspot_raw_companies import HubspotRawCompanies
from app.models.team import PlanCode
from utils.extract_domain import extract_full_domain_url


def hubspot_manual_pull_log_detail(
    manual_log_id: Optional[int],
    db: Session,
    current_user: UserBase,
    listing_plan_code: PlanCode,
):
    hubspot_connection = db.exec(
        select(HubspotIntergrations).where(
            HubspotIntergrations.team_id == current_user.team_id,
            HubspotIntergrations.deleted_at.is_(None),
        )
    ).first()

    if not hubspot_connection:
        raise NotFoundException(detail="integration.hubspot.notFoundConnection")

    company_pull = db.exec(
        select(HubspotCompanyPullHistories, HubspotRawCompanies)
        .join(
            HubspotRawCompanies,
            and_(
                HubspotRawCompanies.integration_id == hubspot_connection.id,
                HubspotRawCompanies.hubspot_team_id
                == hubspot_connection.hubspot_team_id,
                HubspotRawCompanies.hubspot_company_id
                == HubspotCompanyPullHistories.hubspot_company_id,
            ),
        )
        .where(HubspotCompanyPullHistories.id == manual_log_id)
    ).first()

    if not company_pull:
        raise NotFoundException(detail="common.notFound")

    company, raw_company = company_pull

    if company.error_type == "NOT_FOUND":
        return HubspotManualPullLogsDetailResponse(
            total=0,
            hubspot_company_id=(
                int(company.hubspot_company_id) if company.hubspot_company_id else None
            ),
            hubspot_company_name=(
                raw_company.data.get("name") if raw_company.data else None
            ),
            created_at=company.created_at,
            error_type=company.error_type,
            data=[],
        )
    elif company.error_type == "MULTIPLE":
        data = []
        detail = db.exec(
            select(HubspotCompanyMultiplePullHistories).where(
                HubspotCompanyMultiplePullHistories.hubspot_pull_log_id == manual_log_id
            )
        ).first()
        if not detail:
            raise NotFoundException(detail="common.notFound")

        for corporate_number in detail.matched_company_ids:
            ss_company = db.exec(
                select(Company).where(Company.corporate_number == corporate_number)
            ).first()
            domain_url = extract_full_domain_url(ss_company.hp_url)
            if domain_url:
                favicon_url = f"{domain_url}/favicon.ico"
            else:
                favicon_url = None
            if listing_plan_code == PlanCode.UNLIMITED:
                data.append(
                    HubspotManualPullLogsDetail(
                        ss_corporate_number=corporate_number,
                        ss_company_name=ss_company.name,
                        domain=ss_company.domain,
                        is_downloaded=True,
                        favicon_url=favicon_url,
                        president_name=ss_company.president_name,
                    )
                )
            else:
                corporate_numbers_downloaded = db.exec(
                    select(TeamCompany.corporate_number).where(
                        TeamCompany.corporate_number == corporate_number,
                        TeamCompany.deleted_at.is_(None),
                        TeamCompany.team_id == current_user.team_id,
                    )
                ).all()

                is_downloaded = len(corporate_numbers_downloaded) > 0
                data.append(
                    HubspotManualPullLogsDetail(
                        ss_corporate_number=corporate_number,
                        ss_company_name=ss_company.name,
                        domain=ss_company.domain,
                        is_downloaded=is_downloaded,
                        favicon_url=favicon_url,
                        president_name=ss_company.president_name,
                    )
                )

        return HubspotManualPullLogsDetailResponse(
            total=len(data),
            hubspot_company_id=(
                int(company.hubspot_company_id) if company.hubspot_company_id else None
            ),
            hubspot_company_name=(
                raw_company.data.get("name") if raw_company.data else None
            ),
            created_at=company.created_at,
            error_type=company.error_type,
            data=data,
        )
