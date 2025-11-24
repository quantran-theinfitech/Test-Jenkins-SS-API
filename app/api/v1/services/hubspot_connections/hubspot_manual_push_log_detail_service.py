from typing import Optional

from sqlmodel import Session, select

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.hubspot_connections import (
    HubspotManualPushLogsDetail,
    HubspotManualPushLogsDetailResponse,
)
from app.api.v1.schemas.users import UserBase
from app.models import (
    HubspotCompanyMultiplePushHistories,
    HubspotCompanyPushHistories,
    HubspotIntergrations,
)
from app.models.company import Company
from app.models.team import PlanCode
from app.models.team_company import TeamCompany
from utils.hubspot_connection import HubSpotService


def hubspot_manual_push_log_detail(
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

    company_push = db.exec(
        select(HubspotCompanyPushHistories).where(
            HubspotCompanyPushHistories.id == manual_log_id
        )
    ).first()

    if not company_push:
        raise NotFoundException(detail="common.notFound")

    ss_company = db.exec(
        select(Company).where(Company.corporate_number == company_push.ss_company_id)
    ).first()

    if not ss_company:
        raise NotFoundException(detail="common.notFoundCompany")

    if listing_plan_code != PlanCode.UNLIMITED:
        company_downloaded = db.exec(
            select(TeamCompany).where(
                TeamCompany.corporate_number == company_push.ss_company_id
            )
        ).all()
        downloaded_flag = len(company_downloaded) > 0
    else:
        downloaded_flag = True

    if company_push.error_type == "NOT_FOUND":
        return HubspotManualPushLogsDetailResponse(
            total=0,
            ss_corporate_number=company_push.ss_company_id,
            ss_company_name=ss_company.name,
            is_downloaded=downloaded_flag,
            created_at=company_push.created_at,
            error_type=company_push.error_type,
            data=[],
        )
    if company_push.error_type == "MULTIPLE":
        data = []
        hubspot_client = HubSpotService(
            hubspot_connection.access_token, hubspot_connection.refresh_token
        )
        multi_company_hubspot = db.exec(
            select(HubspotCompanyMultiplePushHistories.matched_company_ids).where(
                HubspotCompanyMultiplePushHistories.hubspot_push_log_id == manual_log_id
            )
        ).first()
        for hubspot_company_id in multi_company_hubspot:
            company_info = hubspot_client.get_company_by_id(hubspot_company_id)
            data.append(
                HubspotManualPushLogsDetail(
                    hubspot_company_id=company_info.id,
                    hubspot_company_name=company_info.properties.get("name") or None,
                    domain=company_info.properties.get("domain") or None,
                )
            )
        return HubspotManualPushLogsDetailResponse(
            total=len(data),
            ss_corporate_number=company_push.ss_company_id,
            ss_company_name=ss_company.name,
            is_downloaded=downloaded_flag,
            created_at=company_push.created_at,
            error_type=company_push.error_type,
            data=data,
        )
