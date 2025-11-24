from typing import List

from fastapi import HTTPException
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.constant.constants import INTEGRATION_PLATFORM_ENUM
from app.db import engine
from app.models import (
    SalesforceCompanyFieldMappings,
    SalesforceCompanyPullHistories,
    SalesforceRawCompanies,
    SalesforceSyncHistories,
)
from app.models.integration.hubspot.hubspot_company_field_mappings import (
    HubspotCompanyFieldMappings,
)
from app.models.integration.hubspot.hubspot_company_pull_histories import (
    HubspotCompanyPullHistories,
)
from app.models.integration.hubspot.hubspot_company_sync_histories import (
    HubspotCompanySyncHistories,
)
from app.models.integration.hubspot.hubspot_raw_companies import HubspotRawCompanies
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from utils.hubspot_connection import HubSpotService
from utils.identify.schema import (
    HubspotCompany,
    IdentifyAction,
    IdentifyResult,
    SalesforceCompany,
)
from utils.identify.utils import (
    build_salesforce_synced_companies_mapping,
    build_synced_companies_mapping,
    extract_domain_url,
    get_intergration,
    get_salesforce_synced_companies,
    get_synced_companies,
    normalize_company_name,
    query_matched_companies,
)
from utils.integration.salesforce import SalesforceService

identify_patterns = [["name", "domain"], ["domain"], ["name"]]


def match_pull_companies(db, hubspot_company: HubspotCompany):
    print("_______ start func match_pull_companies _______")
    try:
        matched_companies = query_matched_companies(
            db,
            hubspot_company.name if hubspot_company.name is not None else "",
            hubspot_company.domain if hubspot_company.domain is not None else "",
        )

        result = []

        for identify_pattern in identify_patterns:
            result = []
            for matched_company in matched_companies:
                match_flag = True
                for col in identify_pattern:
                    if not matched_company.__dict__[col]:
                        match_flag = False
                        break
                    if not hubspot_company.__dict__[col]:
                        match_flag = False
                        break
                    if matched_company.__dict__[col] != hubspot_company.__dict__[col]:
                        match_flag = False
                        break
                if match_flag:
                    result.append(matched_company.corporate_number)
            if result:
                break
        return result
    except HTTPException as e:
        print("_______ error of func match_pull_companies _______", str(e))
        raise e


def pull_identify(
    integration_id: int,
    platform: str = INTEGRATION_PLATFORM_ENUM["HUBSPOT"],
) -> List[IdentifyResult]:
    print("_______ start func pull_identify _______")
    print("_______ platform _______", platform)
    try:
        with Session(engine) as db:
            result = []
            if platform == INTEGRATION_PLATFORM_ENUM["HUBSPOT"]:
                hubspot_integration = get_intergration(
                    db=db, integration_id=integration_id, platform=platform
                )
                access_token, refresh_token = (
                    hubspot_integration.access_token,
                    hubspot_integration.refresh_token,
                )
                client = HubSpotService(
                    access_token=access_token, refresh_token=refresh_token
                )

                hubspot_companies = []
                hubspot_raw_companies = []

                field_mappings = db.exec(
                    select(HubspotCompanyFieldMappings).where(
                        HubspotCompanyFieldMappings.integration_id == integration_id,
                        HubspotCompanyFieldMappings.hubspot_team_id
                        == hubspot_integration.hubspot_team_id,
                    )
                ).all()

                hubspot_field_properties = [
                    field_mapping.hubspot_field
                    for field_mapping in field_mappings
                    if field_mapping.hubspot_field
                ]

                list_all_companies = client.get_all_companies(
                    properties=hubspot_field_properties
                )

                if list_all_companies and len(list_all_companies) > 0:
                    for company in list_all_companies:
                        company_marked_done = db.exec(
                            select(HubspotCompanyPullHistories)
                            .join(
                                HubspotCompanySyncHistories,
                                HubspotCompanySyncHistories.log_id
                                == HubspotCompanyPullHistories.log_id,
                            )
                            .where(
                                HubspotCompanyPullHistories.hubspot_company_id
                                == company.id,
                                HubspotCompanySyncHistories.integration_id
                                == integration_id,
                                HubspotCompanyPullHistories.deleted_at.isnot(None),
                            )
                        ).first()

                        if company_marked_done:
                            continue
                        else:
                            hubspot_companies.append(
                                HubspotCompany(
                                    id=company.id,
                                    name=normalize_company_name(
                                        company.properties.get("name")
                                    ),
                                    domain=extract_domain_url(
                                        company.properties.get("domain")
                                    ),
                                )
                            )
                            hubspot_raw_companies.append(
                                HubspotRawCompanies(
                                    hubspot_company_id=company.id,
                                    integration_id=integration_id,
                                    hubspot_team_id=hubspot_integration.hubspot_team_id,
                                    data=company.properties,
                                ).dict()
                            )

                synced_companies = get_synced_companies(
                    db, integration_id=integration_id
                )
                synced_companies_mapping = build_synced_companies_mapping(
                    synced_companies,
                    key_column="hubspot_company_id",
                    value_column="ss_company_id",
                )

                hubspot_raw_companies_dicts = [
                    {k: v for k, v in company.items() if k != "id"}
                    for company in hubspot_raw_companies
                ]
                stmt = insert(HubspotRawCompanies).values(hubspot_raw_companies_dicts)

                stmt = stmt.on_conflict_do_update(
                    constraint="hubspot_raw_companies_unique_key",
                    set_={
                        x.name: getattr(stmt.excluded, x.name)
                        for x in HubspotRawCompanies.metadata.tables[
                            "hubspot_raw_companies"
                        ].columns
                        if x.name != "id"
                    },
                )

                db.execute(stmt)
                db.commit()

                for hubspot_company in hubspot_companies:
                    if synced_companies_mapping.get(hubspot_company.id):
                        continue
                    result.append(
                        IdentifyResult(
                            source_id=hubspot_company.id,
                            target_ids=match_pull_companies(db, hubspot_company),
                            action=IdentifyAction.PULL,
                        )
                    )

            if platform == INTEGRATION_PLATFORM_ENUM["SALESFORCE"]:
                sf_integration = db.exec(
                    select(SalesforceIntegrations).where(
                        SalesforceIntegrations.id == integration_id,
                        SalesforceIntegrations.deleted_at.is_(None),
                    )
                ).first()

                salesforce_service = SalesforceService(
                    access_token=sf_integration.access_token,
                    refresh_token=sf_integration.refresh_token,
                    id_url=sf_integration.id_url,
                    instance_url=sf_integration.instance_url,
                )

                salesforce_companies = []
                salesforce_raw_companies = []

                field_mappings = db.exec(
                    select(SalesforceCompanyFieldMappings).where(
                        SalesforceCompanyFieldMappings.salesforce_integration_id
                        == integration_id,
                        SalesforceCompanyFieldMappings.salesforce_team_id
                        == sf_integration.salesforce_team_id,
                        SalesforceCompanyFieldMappings.deleted_at.is_(None),
                    )
                ).all()

                salesforce_field_properties = [
                    field_mapping.salesforce_field
                    for field_mapping in field_mappings
                    if field_mapping.salesforce_field
                ]

                list_all_companies = salesforce_service.get_all_companies(
                    properties=salesforce_field_properties
                )

                if list_all_companies and len(list_all_companies) > 0:
                    for company in list_all_companies:
                        company_marked_done = db.exec(
                            select(SalesforceCompanyPullHistories)
                            .join(
                                SalesforceSyncHistories,
                                SalesforceSyncHistories.log_id
                                == SalesforceCompanyPullHistories.log_id,
                            )
                            .where(
                                SalesforceCompanyPullHistories.salesforce_company_id
                                == company.get("Id"),
                                SalesforceSyncHistories.salesforce_integration_id
                                == integration_id,
                                SalesforceCompanyPullHistories.deleted_at.isnot(None),
                            )
                        ).first()

                        if company_marked_done:
                            continue
                        else:
                            salesforce_team_id = sf_integration.salesforce_team_id
                            if (
                                salesforce_team_id
                                and company.get("Id")
                                and integration_id
                            ):
                                salesforce_companies.append(
                                    SalesforceCompany(
                                        id=company.get("Id"),
                                        name=normalize_company_name(
                                            company.get("Name")
                                        ),
                                        domain=extract_domain_url(
                                            company.get("Website")
                                        ),
                                    )
                                )
                                salesforce_raw_companies.append(
                                    SalesforceRawCompanies(
                                        salesforce_company_id=company.get("Id"),
                                        salesforce_integration_id=integration_id,
                                        data=company,
                                        salesforce_team_id=salesforce_team_id,
                                    ).dict()
                                )
                            else:
                                continue

                salesforce_synced_companies = get_salesforce_synced_companies(
                    db=db, integration_id=integration_id
                )

                synced_companies_mapping = build_salesforce_synced_companies_mapping(
                    synced_companies=salesforce_synced_companies,
                    key_column="salesforce_company_id",
                    value_column="ss_company_id",
                )

                if salesforce_raw_companies and len(salesforce_raw_companies) > 0:
                    salesforce_raw_companies_dicts = [
                        {k: v for k, v in company.items() if k != "id"}
                        for company in salesforce_raw_companies
                    ]

                    stmt = insert(SalesforceRawCompanies).values(
                        salesforce_raw_companies_dicts
                    )

                    stmt = stmt.on_conflict_do_update(
                        constraint="salesforce_raw_companies_unique_key",
                        set_={
                            x.name: getattr(stmt.excluded, x.name)
                            for x in SalesforceRawCompanies.metadata.tables[
                                "salesforce_raw_companies"
                            ].columns
                            if x.name != "id"
                        },
                    )

                    db.execute(stmt)
                    db.commit()

                for salesforce_company in salesforce_companies:
                    if synced_companies_mapping.get(salesforce_company.id):
                        continue
                    result.append(
                        IdentifyResult(
                            source_id=salesforce_company.id,
                            target_ids=match_pull_companies(db, salesforce_company),
                            action=IdentifyAction.PULL_COMPANIES,
                        )
                    )

            print("_______ end func pull_identify _______")
            return result
    except HTTPException as e:
        print("_______ error of func pull_identify _______", str(e))
        db.rollback()
        raise e
    finally:
        print("_______ end func pull_identify _______")
