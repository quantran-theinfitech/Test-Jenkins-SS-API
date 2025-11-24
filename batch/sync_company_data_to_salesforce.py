from fastapi import HTTPException
from sqlmodel import Session, and_, select

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
    SalesforceSyncHistories,
)
from app.models.prefecture import Prefecture
from batch.get_field_value import get_field_value_salesforce
from utils.integration.salesforce import SalesforceService


def sync_company_data_to_salesforce(
    db: Session, log_id: str, ss_company_id: str, salesforce_company_id: str
):
    print("_______ start func sync_company_data_to_salesforce _______")
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
            .where(SalesforceSyncHistories.log_id == log_id)
        ).first()

        salesforce_raw_company_detail = db.exec(
            select(SalesforceRawCompanies).where(
                SalesforceRawCompanies.salesforce_team_id
                == salesforce_connection.salesforce_team_id,
                SalesforceRawCompanies.salesforce_company_id == salesforce_company_id,
                SalesforceRawCompanies.deleted_at.is_(None),
            )
        ).first()

        salesforce_client = SalesforceService(
            access_token=salesforce_connection.access_token,
            refresh_token=salesforce_connection.refresh_token,
            instance_url=salesforce_connection.instance_url,
            id_url=salesforce_connection.id_url,
        )

        field_mappings = db.exec(
            select(SalesforceCompanyFieldMappings).where(
                SalesforceCompanyFieldMappings.salesforce_integration_id
                == salesforce_connection.id,
                SalesforceCompanyFieldMappings.salesforce_team_id
                == salesforce_connection.salesforce_team_id,
                SalesforceCompanyFieldMappings.deleted_at.is_(None),
            )
        ).all()

        ss_company = db.exec(
            select(Company).where(Company.corporate_number == ss_company_id)
        ).first()

        company = salesforce_client.get_company_by_id(
            salesforce_company_id,
            [
                field_mapping.salesforce_field
                for field_mapping in field_mappings
                if field_mapping.salesforce_field is not None
            ],
        )

        properties = {}
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
            if salesforce_raw_company_detail:
                salesforce_raw_company_detail.data = {
                    **(salesforce_raw_company_detail.data or {}),
                    **properties,
                }
                db.add(salesforce_raw_company_detail)
                db.commit()
    except HTTPException as e:
        print("_______ error of func sync_company_data_to_salesforce _______", str(e))
        raise e
