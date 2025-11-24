from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import ConflictException, NotFoundException
from app.api.v1.schemas.hubspot_connections import CreateCompanyHubspotRequest, TypeSync
from app.api.v1.schemas.users import UserBase
from app.constant.constants import INDUSTRIES_CATEGORIES, LISTING_MARKET_CODE
from app.models import (
    City,
    Company,
    HubspotCompanyFieldMappings,
    HubspotCompanyPullHistories,
    HubspotCompanyPushHistories,
    HubspotIntergrations,
    Prefecture,
)
from app.models.integration.hubspot.hubspot_pull_person_histories import (
    HubspotPullPersonHistories,
)
from app.models.integration.hubspot.hubspot_raw_persons import HubspotRawPersons
from app.models.integration.hubspot.hubspot_synced_companies import (
    HubspotSyncedCompanies,
)
from utils.extension import validate_and_clean_domain
from utils.hubspot_connection import HubSpotService


def create_hubspot_company(
    db: Session,
    current_user: UserBase,
    request: CreateCompanyHubspotRequest,
    manual_log_id: int,
):
    if request.downloaded_flag is False:
        raise ConflictException(detail="common.companyIsLock")
    hubspot_connection = db.exec(
        select(HubspotIntergrations).where(
            HubspotIntergrations.team_id == current_user.team_id,
            HubspotIntergrations.deleted_at.is_(None),
        )
    ).first()

    if not hubspot_connection:
        raise NotFoundException(detail="integration.hubspot.notFoundConnection")

    ss_company = db.exec(
        select(Company).where(
            Company.corporate_number == request.ss_company_corporate_number
        )
    ).first()

    if not ss_company:
        raise NotFoundException(detail="common.notFoundCompany")

    company_prefecture = db.exec(
        select(Prefecture.name).where(Prefecture.id == ss_company.nta_prefecture_id)
    ).first()

    company_city = db.exec(
        select(City.name).where(
            City.id == ss_company.nta_city_id,
            City.prefecture_id == ss_company.nta_prefecture_id,
        )
    ).first()

    hubspot_service = HubSpotService(
        access_token=hubspot_connection.access_token,
        refresh_token=hubspot_connection.refresh_token,
    )

    field_mappings = db.exec(
        select(HubspotCompanyFieldMappings).where(
            HubspotCompanyFieldMappings.integration_id == hubspot_connection.id,
            HubspotCompanyFieldMappings.hubspot_team_id
            == hubspot_connection.hubspot_team_id,
        )
    ).all()
    try:
        properties = {}
        for field in field_mappings:
            field_value = None
            if field.field == "nta_city_id":
                field_value = company_city if company_city else None
            elif field.field == "nta_prefecture_id":
                field_value = company_prefecture if company_prefecture else None
            elif field.field == "establish_at":
                field_value = (
                    str(ss_company.establish_at.year)
                    if ss_company.establish_at
                    else None
                )
            elif field.field == "domain" and ss_company.domain:
                domain_value = getattr(ss_company, field.field, "")
                field_value = validate_and_clean_domain(domain_value)
            elif (
                field.field == "industry_code" and ss_company.industry_code is not None
            ):
                field_value = INDUSTRIES_CATEGORIES[ss_company.industry_code]["text"]
            elif (
                field.field == "main_sub_industry_code"
                and ss_company.main_sub_industry_code is not None
            ):
                for industry in INDUSTRIES_CATEGORIES.values():
                    for child in industry.get("child", []):
                        if child["code"] == ss_company.main_sub_industry_code:
                            field_value = child["text"]
                            break
            elif (
                field.field == "listing_market_code"
                and ss_company.listing_market_code is not None
            ):
                field_value = LISTING_MARKET_CODE[ss_company.listing_market_code]
            elif field.field == "is_listed_market":
                field_value = (
                    getattr(ss_company, "listing_market_code", None) is not None
                    and getattr(ss_company, "listing_market_code", None) != "UNLISTED"
                )
            else:
                field_value = (
                    getattr(ss_company, field.field, None) if field.field else None
                )

            if field_value:
                properties[field.hubspot_field] = field_value

        if properties:
            if request.type_create == TypeSync.PUSH_TO_HUBSPOT:
                new_hubspot_company = hubspot_service.create_company(properties)
                history = db.exec(
                    select(HubspotCompanyPushHistories).where(
                        HubspotCompanyPushHistories.id == manual_log_id,
                        HubspotCompanyPushHistories.deleted_at.is_(None),
                    )
                ).first()
                company_synced = HubspotSyncedCompanies(
                    ss_company_id=request.ss_company_corporate_number,
                    integration_id=hubspot_connection.id,
                    hubspot_team_id=hubspot_connection.hubspot_team_id,
                    hubspot_company_id=new_hubspot_company.id,
                    ss_company_fields=None,
                )
                db.add(company_synced)
                db.flush()
                db.refresh(company_synced)
            elif request.type_create == TypeSync.PULL_FROM_HUBSPOT:
                new_hubspot_company = hubspot_service.create_company(properties)
                history = db.exec(
                    select(HubspotCompanyPullHistories).where(
                        HubspotCompanyPullHistories.id == manual_log_id,
                        HubspotCompanyPullHistories.deleted_at.is_(None),
                    )
                ).first()
                company_synced = HubspotSyncedCompanies(
                    ss_company_id=request.ss_company_corporate_number,
                    integration_id=hubspot_connection.id,
                    hubspot_team_id=hubspot_connection.hubspot_team_id,
                    hubspot_company_id=new_hubspot_company.id,
                    ss_company_fields=None,
                )
                db.add(company_synced)
                db.flush()
                db.refresh(company_synced)
            elif request.type_create == TypeSync.IDENTIFY_PERSON:
                history = db.exec(
                    select(HubspotPullPersonHistories).where(
                        HubspotPullPersonHistories.id == manual_log_id,
                        HubspotPullPersonHistories.deleted_at.is_(None),
                    )
                ).first()

                raw_person = db.exec(
                    select(HubspotRawPersons).where(
                        HubspotRawPersons.hubspot_team_id
                        == hubspot_connection.hubspot_team_id,
                        HubspotRawPersons.integration_id == hubspot_connection.id,
                        HubspotRawPersons.hubspot_person_id
                        == request.hubspot_person_id,
                        HubspotRawPersons.deleted_at.is_(None),
                    )
                ).first()

                exist_synced = db.exec(
                    select(HubspotSyncedCompanies).where(
                        HubspotSyncedCompanies.ss_company_id
                        == request.ss_company_corporate_number,
                        HubspotSyncedCompanies.hubspot_team_id
                        == hubspot_connection.hubspot_team_id,
                        HubspotSyncedCompanies.integration_id == hubspot_connection.id,
                        HubspotSyncedCompanies.deleted_at.is_(None),
                    )
                ).first()
                if exist_synced:
                    hubspot_service.update_person_association_id(
                        request.hubspot_person_id, exist_synced.hubspot_company_id
                    )
                else:
                    new_hubspot_company = hubspot_service.create_company(properties)
                    hubspot_service.update_person_association_id(
                        request.hubspot_person_id, new_hubspot_company.id
                    )
                    company_synced = HubspotSyncedCompanies(
                        ss_company_id=request.ss_company_corporate_number,
                        integration_id=hubspot_connection.id,
                        hubspot_team_id=hubspot_connection.hubspot_team_id,
                        hubspot_company_id=new_hubspot_company.id,
                        ss_company_fields=None,
                    )
                    db.add(company_synced)
                    db.flush()
                    db.refresh(company_synced)

                raw_person.deleted_at = datetime.now()
                db.add(raw_person)

            history.error_type = None
            history.deleted_at = datetime.now()
            db.add(history)
            db.flush()
            db.refresh(history)

            db.commit()
    except HTTPException as e:
        db.rollback()
        raise e
    return 1
