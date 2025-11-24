from fastapi import HTTPException
from sqlmodel import Session, and_, select

from app.models.city import City
from app.models.company import Company
from app.models.integration.hubspot.hubspot_company_field_mappings import (
    HubspotCompanyFieldMappings,
)
from app.models.integration.hubspot.hubspot_company_sync_histories import (
    HubspotCompanySyncHistories,
)
from app.models.integration.hubspot.hubspot_integrations import HubspotIntergrations
from app.models.integration.hubspot.hubspot_raw_companies import HubspotRawCompanies
from app.models.prefecture import Prefecture
from batch.get_field_value import get_field_value
from utils.hubspot_connection import HubSpotService


def sync_company_data_to_husbpot(
    db: Session, log_id: str, ss_company_id: str, hubspot_company_id: str
):
    print("_______ start func sync_company_data_to_husbpot _______")
    try:
        hubspot_connection = db.exec(
            select(HubspotIntergrations)
            .join(
                HubspotCompanySyncHistories,
                and_(
                    HubspotIntergrations.id
                    == HubspotCompanySyncHistories.integration_id,
                    HubspotIntergrations.hubspot_team_id
                    == HubspotCompanySyncHistories.hubspot_team_id,
                ),
            )
            .where(HubspotCompanySyncHistories.log_id == log_id)
        ).first()

        hubspot_raw_company_detail = db.exec(
            select(HubspotRawCompanies).where(
                HubspotRawCompanies.hubspot_team_id
                == hubspot_connection.hubspot_team_id,
                HubspotRawCompanies.hubspot_team_id
                == hubspot_connection.hubspot_team_id,
                HubspotRawCompanies.hubspot_company_id == hubspot_company_id,
            )
        ).first()

        hubspot_client = HubSpotService(
            hubspot_connection.access_token, hubspot_connection.refresh_token
        )

        field_mappings = db.exec(
            select(HubspotCompanyFieldMappings).where(
                HubspotCompanyFieldMappings.integration_id == hubspot_connection.id,
                HubspotCompanyFieldMappings.hubspot_team_id
                == hubspot_connection.hubspot_team_id,
            )
        ).all()

        ss_company = db.exec(
            select(Company).where(Company.corporate_number == ss_company_id)
        ).first()

        company = hubspot_client.get_company_by_id(
            hubspot_company_id,
            [
                field_mapping.hubspot_field
                for field_mapping in field_mappings
                if field_mapping.hubspot_field is not None
            ],
        )

        properties = {}
        # Cập nhật các trường trong HubSpot
        for mapping in field_mappings:
            hubspot_field = mapping.hubspot_field
            salesmart_field = mapping.field
            overwrite_flag = mapping.overwrite_flag
            autofill_flag = mapping.autofill_flag

            hubspot_value = company.properties.get(hubspot_field)

            if overwrite_flag or (autofill_flag and not hubspot_value):
                if (
                    salesmart_field == "nta_city_id"
                    or salesmart_field == "nta_prefecture_id"
                ):
                    company_city = None
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

                    company_prefecture = None
                    if ss_company and ss_company.nta_prefecture_id:
                        company_prefecture = db.exec(
                            select(Prefecture.name).where(
                                Prefecture.id == ss_company.nta_prefecture_id
                            )
                        ).first()

                    value = get_field_value(
                        ss_company,
                        company,
                        salesmart_field,
                        hubspot_field,
                        company_city,
                        company_prefecture,
                    )
                else:
                    value = get_field_value(
                        ss_company, company, salesmart_field, hubspot_field
                    )
                if value:
                    properties.update({hubspot_field: value})

        if properties:
            hubspot_client.update_company(hubspot_company_id, properties)
            if hubspot_raw_company_detail:
                hubspot_raw_company_detail.data = {
                    **(hubspot_raw_company_detail.data or {}),
                    **properties,
                }
                db.add(hubspot_raw_company_detail)
                db.commit()
    except HTTPException as e:
        print("_______ error of func sync_company_data_to_husbpot _______", str(e))
        raise e
