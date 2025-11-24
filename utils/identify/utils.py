# flake8: noqa: E501
from typing import List

import tldextract
from phonenumbers import PhoneNumberFormat, format_number, parse
from sqlmodel import Session, select, text

from app.constant.constants import INTEGRATION_PLATFORM_ENUM
from app.models.integration.hubspot.hubspot_integrations import HubspotIntergrations
from app.models.integration.hubspot.hubspot_synced_companies import (
    HubspotSyncedCompanies,
)
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from app.models.integration.salesforce.salesforce_synced_companies import (
    SalesforceSyncedCompanies,
)
from utils.identify.schema import SSCompany


def normalize_company_name(name: str):
    if name is None:
        return None

    import unicodedata

    name = name.replace("‐", "-")
    name = unicodedata.normalize("NFKC", name)

    remove_list = list(
        {
            "株式会社",
            "(株)",
            "有限会社",
            "(有)",
            "合同会社",
            "(同)",
            "合資会社",
            "(資)",
            "合名会社",
            "(名)",
            "(医療法人財団)",
            "医療法人社団",
            "(公益財団法人)",
            "公益財団法人",
            "(医療法人)",
            "医療法人",
            "医療法人社団慶北会",
        }
    )
    for remove_str in remove_list:
        name = name.replace(remove_str, "")

    import re

    name = re.sub(r"\(.*?\)", "", name)
    return name.strip()


def query_matched_companies(db: Session, name: str, domain: str):
    matched_companies = db.exec(
        text(
            """SELECT corporate_number, normalized_name, domain
            FROM companies
            WHERE
                normalized_name = :company_name
                OR domain = :domain
            ORDER BY CASE WHEN domain = :domain THEN 1 ELSE 0 END DESC;
            """
        ),
        params={"company_name": name, "domain": domain},
    ).all()
    matched_companies = [
        SSCompany(
            corporate_number=c.corporate_number, name=c.normalized_name, domain=c.domain
        )
        for c in matched_companies
    ]
    return matched_companies


def extract_domain(email: str):
    return email.split("@")[-1]


def extract_domain_url(hp_url: str):
    if not hp_url:
        return None
    extract = tldextract.extract(hp_url, include_psl_private_domains=True)
    if not extract.suffix:
        if not extract.domain:
            return None
        return extract.domain
    if not extract.domain:
        return extract.suffix
    return f"{extract.domain}.{extract.suffix}"


def get_intergration(
    db: Session,
    integration_id: int,
    platform: str = INTEGRATION_PLATFORM_ENUM["HUBSPOT"],
):
    if platform == INTEGRATION_PLATFORM_ENUM["HUBSPOT"]:
        return db.exec(
            select(HubspotIntergrations).where(
                HubspotIntergrations.id == integration_id,
                HubspotIntergrations.deleted_at.is_(None),
            )
        ).first()

    if platform == INTEGRATION_PLATFORM_ENUM["SALESFORCE"]:
        return db.exec(
            select(SalesforceIntegrations).where(
                SalesforceIntegrations.id == integration_id,
                SalesforceIntegrations.deleted_at.is_(None),
            )
        ).first()


def get_synced_companies(
    db: Session, integration_id: int
) -> List[HubspotSyncedCompanies]:
    return db.exec(
        select(HubspotSyncedCompanies).where(
            HubspotSyncedCompanies.integration_id == integration_id,
            HubspotSyncedCompanies.deleted_at.is_(None),
        )
    ).all()


def build_synced_companies_mapping(
    synced_companies: List[HubspotSyncedCompanies], key_column: str, value_column: str
):
    return {
        company.__dict__[key_column]: company.__dict__[value_column]
        for company in synced_companies
    }


def get_salesforce_synced_companies(
    db: Session, integration_id: int
) -> List[SalesforceSyncedCompanies]:
    return db.exec(
        select(SalesforceSyncedCompanies).where(
            SalesforceSyncedCompanies.salesforce_integration_id == integration_id,
            SalesforceSyncedCompanies.deleted_at.is_(None),
        )
    ).all()


def build_salesforce_synced_companies_mapping(
    synced_companies: List[SalesforceSyncedCompanies],
    key_column: str,
    value_column: str,
):
    return {
        company.__dict__[key_column]: company.__dict__[value_column]
        for company in synced_companies
    }


def normalize_tel(raw_data: str):
    if not raw_data:
        return None

    try:
        tel = format_number(parse(raw_data, "JP"), PhoneNumberFormat.E164)
        return tel
    except:
        return None
