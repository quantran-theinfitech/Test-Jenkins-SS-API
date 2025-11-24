from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.base.exceptions import ConflictException, NotFoundException
from app.api.v1.schemas.hubspot_connections import TypeSync
from app.api.v1.schemas.integration.salesforce import SalesforceCreateCompanyRequest
from app.api.v1.schemas.users import UserBase
from app.constant.constants import INDUSTRIES_CATEGORIES, LISTING_MARKET_CODE
from app.models.city import City
from app.models.company import Company
from app.models.integration.salesforce.salesforce_company_field_mappings import (
    SalesforceCompanyFieldMappings,
)
from app.models.integration.salesforce.salesforce_company_push_histories import (
    SalesforceCompanyPushHistories,
)
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from app.models.integration.salesforce.salesforce_person_pull_histories import (
    SalesforcePersonPullHistories,
)
from app.models.integration.salesforce.salesforce_raw_persons import (
    SalesforceRawPersons,
)
from app.models.integration.salesforce.salesforce_synced_companies import (
    SalesforceSyncedCompanies,
)
from app.models.prefecture import Prefecture
from utils.extension import validate_and_clean_domain
from utils.integration.salesforce import SalesforceService


def create_salesforce_company(
    error_log_id: int,
    db: Session,
    current_user: UserBase,
    request: SalesforceCreateCompanyRequest,
):
    if request.downloaded_flag is False:
        raise ConflictException(detail="common.companyIsLock")

    salesforce_connection = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == current_user.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    if not salesforce_connection:
        raise NotFoundException(detail="common.notFound")

    ss_company = db.exec(
        select(Company).where(
            Company.corporate_number == request.ss_company_corporate_number
        )
    ).first()

    if not ss_company:
        raise NotFoundException(detail="common.notFound")

    company_prefecture = db.exec(
        select(Prefecture.name).where(Prefecture.id == ss_company.nta_prefecture_id)
    ).first()

    company_city = db.exec(
        select(City.name).where(
            City.id == ss_company.nta_city_id,
            City.prefecture_id == ss_company.nta_prefecture_id,
        )
    ).first()

    field_mappings = db.exec(
        select(SalesforceCompanyFieldMappings).where(
            SalesforceCompanyFieldMappings.salesforce_integration_id
            == salesforce_connection.id,
            SalesforceCompanyFieldMappings.salesforce_team_id
            == salesforce_connection.salesforce_team_id,
            SalesforceCompanyFieldMappings.team_id == current_user.team_id,
            SalesforceCompanyFieldMappings.deleted_at.is_(None),
        )
    ).all()

    salesforce_service = SalesforceService(
        access_token=salesforce_connection.access_token,
        refresh_token=salesforce_connection.refresh_token,
        instance_url=salesforce_connection.instance_url,
        id_url=salesforce_connection.id_url,
    )

    try:
        properties = {}
        for mapping in field_mappings:
            field_value = None
            if mapping.field == "nta_city_id":
                field_value = company_city if company_city else None
            elif mapping.field == "nta_prefecture_id":
                field_value = company_prefecture if company_prefecture else None
            elif mapping.field == "establish_at":
                field_value = (
                    str(ss_company.establish_at.year)
                    if ss_company.establish_at
                    else None
                )
            elif mapping.field == "domain" and ss_company.domain:
                domain_value = getattr(ss_company, mapping.field, "")
                field_value = validate_and_clean_domain(domain_value)
            elif (
                mapping.field == "industry_code"
                and ss_company.industry_code is not None
            ):
                field_value = INDUSTRIES_CATEGORIES[ss_company.industry_code]["text"]
            elif (
                mapping.field == "main_sub_industry_code"
                and ss_company.main_sub_industry_code is not None
            ):
                for industry in INDUSTRIES_CATEGORIES.values():
                    for child in industry.get("child", []):
                        if child["code"] == ss_company.main_sub_industry_code:
                            field_value = child["text"]
                            break

            elif (
                mapping.field == "listing_market_code"
                and ss_company.listing_market_code is not None
            ):
                field_value = LISTING_MARKET_CODE[ss_company.listing_market_code]
            elif mapping.field == "is_listed_market":
                field_value = (
                    "はい"
                    if getattr(ss_company, "listing_market_code", None) is not None
                    and getattr(ss_company, "listing_market_code", None) != "UNLISTED"
                    else "いいえ"
                )
            else:
                field_value = (
                    getattr(ss_company, mapping.field, None) if mapping.field else None
                )

            if field_value:
                if mapping.salesforce_field == "ShippingAddress":
                    properties["ShippingStreet"] = field_value if field_value else None
                    properties["ShippingPostalCode"] = (
                        ss_company.postal_code if ss_company.postal_code else None
                    )
                    properties["ShippingCity"] = company_city if company_city else None
                    properties["ShippingCountry"] = "Japan"
                elif mapping.salesforce_field == "BillingAddress":
                    properties["BillingStreet"] = field_value if field_value else None
                    properties["BillingPostalCode"] = (
                        ss_company.postal_code
                        if ss_company and ss_company.postal_code
                        else None
                    )
                    properties["BillingCity"] = company_city if company_city else None
                    properties["BillingCountry"] = "Japan"
                else:
                    properties[mapping.salesforce_field] = field_value

        if properties:
            if request.type_create == TypeSync.PUSH_TO_HUBSPOT:
                new_salesforce_company = salesforce_service.create_company(properties)

                history = db.exec(
                    select(SalesforceCompanyPushHistories).where(
                        SalesforceCompanyPushHistories.id == error_log_id,
                        SalesforceCompanyPushHistories.team_id == current_user.team_id,
                        SalesforceCompanyPushHistories.salesforce_integration_id
                        == salesforce_connection.id,
                        SalesforceCompanyPushHistories.deleted_at.is_(None),
                    )
                ).first()
                if not history:
                    raise NotFoundException(detail="common.notFound")

                company_synced = SalesforceSyncedCompanies(
                    ss_company_id=request.ss_company_corporate_number,
                    salesforce_integration_id=salesforce_connection.id,
                    salesforce_team_id=salesforce_connection.salesforce_team_id,
                    salesforce_company_id=new_salesforce_company.get("id"),
                )
                db.add(company_synced)
                db.flush()
                db.refresh(company_synced)
            elif request.type_create == TypeSync.IDENTIFY_PERSON:
                history = db.exec(
                    select(SalesforcePersonPullHistories).where(
                        SalesforcePersonPullHistories.id == error_log_id,
                        SalesforcePersonPullHistories.deleted_at.is_(None),
                    )
                ).first()

                raw_person = db.exec(
                    select(SalesforceRawPersons).where(
                        SalesforceRawPersons.salesforce_team_id
                        == salesforce_connection.salesforce_team_id,
                        SalesforceRawPersons.salesforce_integration_id
                        == salesforce_connection.id,
                        SalesforceRawPersons.salesforce_person_id
                        == history.salesforce_person_id,
                        SalesforceRawPersons.deleted_at.is_(None),
                    )
                ).first()

                exist_synced = db.exec(
                    select(SalesforceSyncedCompanies).where(
                        SalesforceSyncedCompanies.ss_company_id
                        == request.ss_company_corporate_number,
                        SalesforceSyncedCompanies.salesforce_team_id
                        == salesforce_connection.salesforce_team_id,
                        SalesforceSyncedCompanies.salesforce_integration_id
                        == salesforce_connection.id,
                        SalesforceSyncedCompanies.deleted_at.is_(None),
                    )
                ).first()
                if exist_synced:
                    salesforce_service.update_person_account_id(
                        history.salesforce_person_id, exist_synced.salesforce_company_id
                    )
                    history.salesforce_company_id = exist_synced.salesforce_company_id
                else:
                    new_salesforce_company = salesforce_service.create_company(
                        properties
                    )
                    salesforce_service.update_person_account_id(
                        person_id=history.salesforce_person_id,
                        account_id=new_salesforce_company.get("id"),
                    )
                    history.salesforce_company_id = new_salesforce_company.get("id")

                raw_person.deleted_at = datetime.now()
                db.add(raw_person)

            history.deleted_at = datetime.now()
            db.add(history)
            db.commit()
    except HTTPException as e:
        print("_______ e create_salesforce_company _______", e)
        db.rollback()
        raise e
