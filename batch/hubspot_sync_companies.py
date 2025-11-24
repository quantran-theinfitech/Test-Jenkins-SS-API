import uuid
from datetime import datetime
from typing import List

from fastapi import HTTPException
from sqlmodel import Session, and_, select

from app.api.base.exceptions import BadRequestException
from app.db import engine
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
from app.models.integration.hubspot.hubspot_synced_companies import (
    HubspotSyncedCompanies,
)
from app.models.prefecture import Prefecture
from batch.common import parse_arguments
from batch.get_field_value import get_field_value
from utils.hubspot_connection import HubSpotService


def hubspot_sync_companies(args: List[str]):
    print("_______ start func hubspot_sync_companies _______")
    try:
        arguments = parse_arguments(args)
        if "log_id" in arguments:
            handle_hubspot_sync_companies(arguments["log_id"])
        else:
            db = Session(engine)
            hubspots = db.exec(
                select(HubspotIntergrations).where(
                    HubspotIntergrations.deleted_at.is_(None)
                )
            ).all()
            log_ids = []

            for hubspot in hubspots:
                if hubspot.auto_sync_companies:
                    try:
                        hubspot_company_sync = HubspotCompanySyncHistories(
                            hubspot_team_id=hubspot.hubspot_team_id,
                            integration_id=hubspot.id,
                            team_id=hubspot.team_id,
                            type="SYNC",
                            status=0,
                            hubspot_push_type="AUTO",
                            log_id=str(uuid.uuid4()),
                        )
                        db.add(hubspot_company_sync)
                        log_ids.append(hubspot_company_sync.log_id)
                        db.flush()
                    except HTTPException as e:
                        print(
                            "_______ error func hubspot_sync_companies (AUTO) _______",
                            str(e.detail),
                        )
                        continue
                else:
                    continue
            db.commit()
            for log_id in log_ids:
                try:
                    handle_hubspot_sync_companies(log_id)
                except HTTPException as e:
                    print(
                        "_______ error log_id hubspot_sync_companies _______",
                        str(e.detail),
                    )
                    continue
    except HTTPException as e:
        print("_______ error of func hubspot_sync_companies _______", str(e.detail))
        raise e


def handle_hubspot_sync_companies(log_id: str):
    print("_______ start func handle_hubspot_sync_companies _______")
    db = Session(engine)

    sync_history = db.exec(
        select(HubspotCompanySyncHistories).where(
            HubspotCompanySyncHistories.log_id == log_id
        )
    ).first()

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

        if not hubspot_connection:
            raise BadRequestException(detail="integration.hubspot.connectFailed")

        companies = db.exec(
            select(HubspotSyncedCompanies)
            .join(
                HubspotCompanySyncHistories,
                and_(
                    HubspotSyncedCompanies.integration_id
                    == HubspotCompanySyncHistories.integration_id,
                    HubspotSyncedCompanies.hubspot_team_id
                    == HubspotCompanySyncHistories.hubspot_team_id,
                ),
            )
            .where(HubspotCompanySyncHistories.log_id == log_id)
        ).all()

        success_count = 0
        hubspot_client = HubSpotService(
            hubspot_connection.access_token, hubspot_connection.refresh_token
        )

        hubspot_client.get_user_info()

        try:
            for company_synced in companies:
                ss_company = db.exec(
                    select(Company).where(
                        Company.corporate_number == company_synced.ss_company_id
                    )
                ).first()

                field_mappings = db.exec(
                    select(HubspotCompanyFieldMappings).where(
                        HubspotCompanyFieldMappings.integration_id
                        == company_synced.integration_id,
                        HubspotCompanyFieldMappings.hubspot_team_id
                        == company_synced.hubspot_team_id,
                    )
                ).all()

                hubspot_raw_company_detail = db.exec(
                    select(HubspotRawCompanies).where(
                        HubspotRawCompanies.hubspot_team_id
                        == hubspot_connection.hubspot_team_id,
                        HubspotRawCompanies.hubspot_company_id
                        == company_synced.hubspot_company_id,
                    )
                ).first()

                hubspot_company_id = company_synced.hubspot_company_id
                try:
                    company = hubspot_client.get_company_by_id(
                        hubspot_company_id,
                        [
                            field_mapping.hubspot_field
                            for field_mapping in field_mappings
                            if field_mapping.hubspot_field is not None
                        ],
                    )
                except Exception:
                    company_synced.deleted_at = datetime.now()
                    db.add(company_synced)
                    db.commit()
                    continue

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
                                        City.prefecture_id
                                        == ss_company.nta_prefecture_id,
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
                    success_count += 1
                    if hubspot_raw_company_detail:
                        hubspot_raw_company_detail.data = {
                            **(hubspot_raw_company_detail.data or {}),
                            **properties,
                        }
                        db.add(hubspot_raw_company_detail)

            sync_history.sync_count = success_count
            sync_history.status = 1
            db.add(sync_history)
            db.commit()
        except HTTPException as e:
            print(
                "_______ error of func handle_hubspot_sync_companies loop _______",
                str(e.detail),
            )
            db.rollback()
            raise e

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
        print("_______ error of func handle_hubspot_sync_companies _______", error)
        if db and sync_history:
            sync_history.status = 2
            sync_history.error_message = str(error)
            db.add(sync_history)
            db.commit()
        raise e
