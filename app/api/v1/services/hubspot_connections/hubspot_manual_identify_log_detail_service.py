from datetime import datetime
from typing import Optional

from sqlmodel import Session, and_, select

from app.api.base.exceptions import ConflictException, NotFoundException
from app.api.v1.schemas.hubspot_connections import (
    HubspotManualIdentifyLogsDetail,
    HubspotManualIdentifyLogsDetailResponse,
)
from app.api.v1.schemas.users import UserBase
from app.models import TeamCompany
from app.models.company import Company
from app.models.integration.hubspot.hubspot_integrations import HubspotIntergrations
from app.models.integration.hubspot.hubspot_person_multiple_company_histories import (
    HubspotPersonMultipleCompanyHistories,
)
from app.models.integration.hubspot.hubspot_person_not_found_company_histories import (
    HubspotPersonNotFoundHubspotCompanyHistories,
)
from app.models.integration.hubspot.hubspot_pull_person_histories import (
    HubspotPullPersonHistories,
)
from app.models.integration.hubspot.hubspot_raw_persons import HubspotRawPersons
from app.models.team import PlanCode
from utils.extract_domain import extract_full_domain_url
from utils.hubspot_connection import HubSpotService


def hubspot_manual_identify_log_detail(
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

    person_pull = db.exec(
        select(HubspotPullPersonHistories, HubspotRawPersons)
        .join(
            HubspotRawPersons,
            and_(
                HubspotRawPersons.integration_id == hubspot_connection.id,
                HubspotRawPersons.hubspot_team_id == hubspot_connection.hubspot_team_id,
                HubspotRawPersons.hubspot_person_id
                == HubspotPullPersonHistories.hubspot_person_id,
            ),
        )
        .where(HubspotPullPersonHistories.id == manual_log_id)
    ).first()

    if not person_pull:
        raise NotFoundException(detail="common.notFound")

    person_data, raw_person = person_pull

    hubspot_client = HubSpotService(
        hubspot_connection.access_token, hubspot_connection.refresh_token
    )
    person = hubspot_client.get_person_by_id(person_data.hubspot_person_id)

    if person.associations is not None:
        person_data.deleted_at = datetime.now()
        db.add(person_data)

        raw_person.deleted_at = datetime.now()
        db.add(raw_person)

        db.commit()
        raise ConflictException(detail="integration.hubspot.errorLog.personHasCompany")
    else:
        company = None

    data = []

    if person_data.error_type == "NOT_FOUND":
        return HubspotManualIdentifyLogsDetailResponse(
            total=0,
            hubspot_person_id=person_data.hubspot_person_id,
            hub_person_name=(
                (raw_person.data.get("firstname") or "")
                + (raw_person.data.get("lastname") or "")
                if raw_person.data
                else None
            ),
            hubspot_company_id=company.id if company else None,
            hubspot_company_name=company.properties.get("name") if company else None,
            created_at=person_data.created_at,
            error_type=person_data.error_type,
            data=[],
        )
    elif person_data.error_type == "MULTIPLE":
        detail = db.exec(
            select(HubspotPersonMultipleCompanyHistories).where(
                HubspotPersonMultipleCompanyHistories.hubspot_person_log_id
                == manual_log_id
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
                    HubspotManualIdentifyLogsDetail(
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
                    HubspotManualIdentifyLogsDetail(
                        ss_corporate_number=corporate_number,
                        ss_company_name=ss_company.name,
                        domain=ss_company.domain,
                        is_downloaded=is_downloaded,
                        favicon_url=favicon_url,
                        president_name=ss_company.president_name,
                    )
                )
    elif person_data.error_type == "NOT_COMPANY":
        detail = db.exec(
            select(HubspotPersonNotFoundHubspotCompanyHistories).where(
                HubspotPersonNotFoundHubspotCompanyHistories.hubspot_person_log_id
                == manual_log_id
            )
        ).first()

        if not detail:
            raise NotFoundException(detail="common.notFound")
        ss_company = db.exec(
            select(Company).where(Company.corporate_number == detail.ss_company_id)
        ).first()
        domain_url = extract_full_domain_url(ss_company.hp_url)
        if domain_url:
            favicon_url = f"{domain_url}/favicon.ico"
        else:
            favicon_url = None
        if listing_plan_code == PlanCode.UNLIMITED:
            data.append(
                HubspotManualIdentifyLogsDetail(
                    ss_corporate_number=detail.ss_company_id,
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
                    TeamCompany.corporate_number == detail.ss_company_id,
                    TeamCompany.deleted_at.is_(None),
                    TeamCompany.team_id == current_user.team_id,
                )
            ).all()

            is_downloaded = len(corporate_numbers_downloaded) > 0
            data.append(
                HubspotManualIdentifyLogsDetail(
                    ss_corporate_number=ss_company.corporate_number,
                    ss_company_name=ss_company.name,
                    domain=ss_company.domain,
                    is_downloaded=is_downloaded,
                    favicon_url=favicon_url,
                    president_name=ss_company.president_name,
                )
            )
    return HubspotManualIdentifyLogsDetailResponse(
        total=len(data),
        hubspot_person_id=person_data.hubspot_person_id,
        hub_person_name=(
            (raw_person.data.get("firstname") or "")
            + (raw_person.data.get("lastname") or "")
            if raw_person.data
            else None
        ),
        hubspot_company_id=company.id if company else None,
        hubspot_company_name=company.properties.get("name") if company else None,
        created_at=person_data.created_at,
        error_type=person_data.error_type,
        data=data,
    )
