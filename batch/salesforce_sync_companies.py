import uuid
from datetime import datetime
from typing import List

from fastapi import HTTPException
from sqlmodel import Session, and_, select

from app.api.base.exceptions import BadRequestException
from app.db import engine
from app.models.city import City
from app.models.company import Company
from app.models.integration.salesforce.salesforce_company_field_mappings import (
    SalesforceCompanyFieldMappings,
)
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from app.models.integration.salesforce.salesforce_raw_companies import (
    SalesforceRawCompanies,
)
from app.models.integration.salesforce.salesforce_sync_histories import (
    TYPE_INTEGRATION_ENUM,
    SalesforceSyncHistories,
)
from app.models.integration.salesforce.salesforce_synced_companies import (
    SalesforceSyncedCompanies,
)
from app.models.prefecture import Prefecture
from batch.common import parse_arguments
from batch.get_field_value import get_field_value_salesforce
from utils.integration.salesforce import SalesforceService


def salesforce_sync_companies(args: List[str]):
    print("_______ start func salesforce_sync_companies _______")
    try:
        arguments = parse_arguments(args)
        if "log_id" in arguments:
            handle_salesforce_sync_companies(arguments["log_id"])
        else:
            db = Session(engine)
            salesforces = db.exec(
                select(SalesforceIntegrations).where(
                    SalesforceIntegrations.deleted_at.is_(None)
                )
            ).all()

            log_ids = []
            for salesforce in salesforces:
                if salesforce.auto_sync_companies:
                    try:
                        salesforce_company_sync = SalesforceSyncHistories(
                            salesforce_team_id=salesforce.salesforce_team_id,
                            salesforce_integration_id=salesforce.id,
                            team_id=salesforce.team_id,
                            type=TYPE_INTEGRATION_ENUM.SYNC_COMPANIES,
                            status=0,
                            method="AUTO",
                            log_id=str(uuid.uuid4()),
                        )
                        db.add(salesforce_company_sync)
                        log_ids.append(salesforce_company_sync.log_id)
                        db.flush()
                    except HTTPException as e:
                        print(
                            """
                                _______ error salesforce_sync_companies (AUTO) _______
                            """,
                            str(e.detail),
                        )
                        continue
                else:
                    continue
            db.commit()

            for log_id in log_ids:
                try:
                    handle_salesforce_sync_companies(log_id)
                except HTTPException as e:
                    print(
                        "_______ error log_id salesforce_sync_companies _______",
                        str(e.detail),
                    )
                    continue
    except HTTPException as e:
        print("_______ error of func salesforce_sync_companies _______", str(e.detail))
        raise e


def handle_salesforce_sync_companies(log_id: str):
    print("_______ start func handle_salesforce_sync_companies _______")
    db = Session(engine)

    sync_history = db.exec(
        select(SalesforceSyncHistories).where(
            SalesforceSyncHistories.log_id == log_id,
            SalesforceSyncHistories.deleted_at.is_(None),
        )
    ).first()

    try:
        salesforce_connection = db.exec(
            select(SalesforceIntegrations)
            .join(
                SalesforceSyncHistories,
                and_(
                    SalesforceIntegrations.id
                    == SalesforceSyncHistories.salesforce_integration_id,
                    SalesforceIntegrations.salesforce_team_id
                    == SalesforceSyncHistories.salesforce_team_id,
                ),
            )
            .where(
                SalesforceSyncHistories.log_id == log_id,
                SalesforceIntegrations.deleted_at.is_(None),
                SalesforceSyncHistories.deleted_at.is_(None),
            )
        ).first()

        if not salesforce_connection:
            raise BadRequestException(detail="integration.salesforce.connectFailed")

        synced_companies = db.exec(
            select(SalesforceSyncedCompanies)
            .join(
                SalesforceSyncHistories,
                and_(
                    SalesforceSyncedCompanies.salesforce_integration_id
                    == SalesforceSyncHistories.salesforce_integration_id,
                    SalesforceSyncedCompanies.salesforce_team_id
                    == SalesforceSyncHistories.salesforce_team_id,
                ),
            )
            .where(
                SalesforceSyncHistories.log_id == log_id,
                SalesforceSyncedCompanies.deleted_at.is_(None),
                SalesforceSyncHistories.deleted_at.is_(None),
            )
        ).all()

        success_count = 0
        salesforce_client = SalesforceService(
            access_token=salesforce_connection.access_token,
            refresh_token=salesforce_connection.refresh_token,
            instance_url=salesforce_connection.instance_url,
            id_url=salesforce_connection.id_url,
        )

        salesforce_client.check_api_enabled()

        for company_synced in synced_companies:
            ss_company = db.exec(
                select(Company).where(
                    Company.corporate_number == company_synced.ss_company_id
                )
            ).first()

            field_mappings = db.exec(
                select(SalesforceCompanyFieldMappings).where(
                    SalesforceCompanyFieldMappings.salesforce_integration_id
                    == company_synced.salesforce_integration_id,
                    SalesforceCompanyFieldMappings.salesforce_team_id
                    == company_synced.salesforce_team_id,
                    SalesforceCompanyFieldMappings.deleted_at.is_(None),
                )
            ).all()

            salesforce_raw_company_detail = db.exec(
                select(SalesforceRawCompanies).where(
                    SalesforceRawCompanies.salesforce_team_id
                    == company_synced.salesforce_team_id,
                    SalesforceRawCompanies.salesforce_company_id
                    == company_synced.salesforce_company_id,
                )
            ).first()

            salesforce_company_id = company_synced.salesforce_company_id
            try:
                company = salesforce_client.get_company_by_id(
                    salesforce_company_id,
                    [
                        field_mapping.salesforce_field
                        for field_mapping in field_mappings
                        if field_mapping.salesforce_field is not None
                    ],
                )
            except Exception:
                company_synced.deleted_at = datetime.now()
                db.add(company_synced)
                db.commit()
                continue

            properties = {}
            # Cập nhật các trường trong Salesforce
            for mapping in field_mappings:
                salesforce_field = mapping.salesforce_field
                salesmart_field = mapping.field
                overwrite_flag = mapping.overwrite_flag
                autofill_flag = mapping.autofill_flag

                salesforce_value = company.get(salesforce_field)

                if overwrite_flag or (autofill_flag and not salesforce_value):
                    company_city = None
                    company_prefecture = None
                    if (
                        salesmart_field == "nta_city_id"
                        or salesmart_field == "nta_prefecture_id"
                    ):
                        if (
                            ss_company
                            and ss_company.nta_city_id
                            and ss_company.nta_prefecture_id
                        ):
                            company_city = db.exec(
                                select(City.name).where(
                                    City.id == ss_company.nta_city_id,
                                    City.prefecture_id == ss_company.nta_prefecture_id,
                                )
                            ).first()

                        if ss_company and ss_company.nta_prefecture_id:
                            company_prefecture = db.exec(
                                select(Prefecture.name).where(
                                    Prefecture.id == ss_company.nta_prefecture_id
                                )
                            ).first()

                        value = get_field_value_salesforce(
                            ss_company,
                            company,
                            salesmart_field,
                            salesforce_field,
                            company_city,
                            company_prefecture,
                        )
                    else:
                        value = get_field_value_salesforce(
                            ss_company, company, salesmart_field, salesforce_field
                        )

                    if value:
                        if mapping.salesforce_field == "ShippingAddress":
                            properties["ShippingStreet"] = value if value else None
                            properties["ShippingPostalCode"] = (
                                ss_company.postal_code
                                if ss_company and ss_company.postal_code
                                else None
                            )
                            properties["ShippingCity"] = (
                                company_city if company_city else None
                            )
                            properties["ShippingCountry"] = "Japan"
                        elif mapping.salesforce_field == "BillingAddress":
                            properties["BillingStreet"] = value if value else None
                            properties["BillingPostalCode"] = (
                                ss_company.postal_code
                                if ss_company and ss_company.postal_code
                                else None
                            )
                            properties["BillingCity"] = (
                                company_city if company_city else None
                            )
                            properties["BillingCountry"] = "Japan"
                        else:
                            properties.update({salesforce_field: value})

            if properties:
                salesforce_client.update_company(salesforce_company_id, properties)
                success_count += 1
                if salesforce_raw_company_detail:
                    salesforce_raw_company_detail.data = {
                        **(salesforce_raw_company_detail.data or {}),
                        **properties,
                    }
                    db.add(salesforce_raw_company_detail)

        sync_history.sync_count = success_count
        sync_history.status = 1
        db.add(sync_history)
        db.commit()
    except HTTPException as e:
        error = None
        if hasattr(e, "content"):
            error = e.content
        elif hasattr(e, "body"):
            error = e.body
        elif hasattr(e, "detail"):
            error = e.detail
        elif hasattr(e, "response") and hasattr(e.response, "text"):
            error = e.response.text
        else:
            error = str(e)
        print("_______ error of func handle_salesforce_sync_companies _______", error)
        if db and sync_history:
            sync_history.status = 2
            sync_history.error_message = str(error)
            db.add(sync_history)
            db.commit()
        raise e
