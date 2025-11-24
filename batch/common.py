from datetime import datetime
from typing import Dict, List

import sqlalchemy
from elasticsearch import ConflictError, Elasticsearch
from elasticsearch_dsl import Q, UpdateByQuery
from fastapi import HTTPException
from sqlmodel import Session, col, select

from app.api.base.exceptions import (
    BadRequestException,
    ConflictException,
    PaymentRequiredException,
)
from app.api.v1.schemas.elasticsearch.companies_extend import EsCompanyExtend
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.base_service import remaining_credit
from app.config import settings
from app.es import es_basic_auth, es_url
from app.models import (
    HubspotCompanyMultiplePullHistories,
    HubspotCompanyMultiplePushHistories,
    HubspotCompanyNotFoundPullHistories,
    HubspotCompanyNotFoundPushHistories,
    HubspotCompanyPullHistories,
    HubspotCompanyPushHistories,
    HubspotCompanySyncHistories,
    HubspotPersonMultipleCompanyHistories,
    HubspotPersonNotFoundHubspotCompanyHistories,
    HubspotPullPersonHistories,
    HubspotSyncedCompanies,
    SalesforceCompanyMultiplePullHistories,
    SalesforceCompanyMultiplePushHistories,
    SalesforceCompanyNotFoundPullHistories,
    SalesforceCompanyNotFoundPushHistories,
    SalesforceCompanyPullHistories,
    SalesforceCompanyPushHistories,
    SalesforceIntegrations,
    SalesforcePersonMultiplePullHistories,
    SalesforcePersonNotFoundPullHistories,
    SalesforcePersonPullHistories,
    SalesforceSyncedCompanies,
    SalesforceSyncHistories,
)
from app.models.downloaded_histories import DownloadedHistory
from app.models.integration.salesforce.salesforce_sync_histories import (
    TYPE_INTEGRATION_ENUM,
)
from app.models.team import PlanCode, Team
from app.models.team_company import StatusCode, TeamCompany
from app.models.team_credit import ServiceCode
from app.models.user import User
from batch.sync_company_data_to_hubspot import sync_company_data_to_husbpot
from batch.sync_company_data_to_salesforce import sync_company_data_to_salesforce
from utils.credit_utils import consume_credit, is_enough_credit
from utils.hubspot_connection import HubSpotService, create_hubspot_company
from utils.identify.schema import (
    IdentifyAction,
    IdentifyResult,
    SalesforceIdentifyResult,
)
from utils.identify.utils import get_intergration
from utils.integration.salesforce import SalesforceService, create_salesforce_company


def parse_arguments(args: List[str]) -> Dict:
    args_dict = {}
    for arg in args:
        if not arg.startswith("--"):
            print(f"Invalid argument: {arg}")
            continue
        parts = arg.split("=")
        args_dict[parts[0].strip("--")] = parts[1] if len(parts) > 1 else True
    return args_dict


def handle_pull_person_item(
    db: Session, item: IdentifyResult, sync_log_history: HubspotCompanySyncHistories
):
    print("_______ start func handle_pull_person_item _______")
    try:
        print("HANDLE PULL PERSON ITEM")
        print("---------- item -----------", item)
        ret = []
        pull_history = HubspotPullPersonHistories()
        pull_history.log_id = sync_log_history.log_id
        pull_history.hubspot_person_id = item.source_id
        db.add(pull_history)
        db.flush()
        if len(item.target_ids) == 0:
            pull_history.error_type = "NOT_FOUND"
        if len(item.target_ids) > 1:
            pull_history.error_type = "MULTIPLE"
            multiple_history = HubspotPersonMultipleCompanyHistories()
            multiple_history.hubspot_person_log_id = pull_history.id
            multiple_history.matched_company_ids = item.target_ids
            ret.append(multiple_history)
        if len(item.target_ids) == 1:
            pull_history.error_type = None
            synced_company = db.exec(
                select(HubspotSyncedCompanies).where(
                    HubspotSyncedCompanies.ss_company_id == item.target_ids[0],
                    HubspotSyncedCompanies.integration_id
                    == sync_log_history.integration_id,
                    HubspotSyncedCompanies.hubspot_team_id
                    == sync_log_history.hubspot_team_id,
                    HubspotSyncedCompanies.deleted_at.is_(None),
                )
            ).first()
            hubspot_integration = get_intergration(
                db, integration_id=sync_log_history.integration_id
            )
            access_token, refresh_token = (
                hubspot_integration.access_token,
                hubspot_integration.refresh_token,
            )
            client = HubSpotService(
                access_token=access_token, refresh_token=refresh_token
            )

            if not synced_company:
                team = db.exec(
                    select(Team).where(Team.id == sync_log_history.team_id)
                ).one()
                if team:
                    is_company_downloaded = db.exec(
                        select(TeamCompany).where(
                            TeamCompany.corporate_number == item.target_ids[0],
                            TeamCompany.team_id == sync_log_history.team_id,
                            TeamCompany.deleted_at.is_(None),
                        )
                    ).first()
                    corporate_numbers_downloaded = []
                    if (
                        team.form_plan_code == PlanCode.UNLIMITED
                        or team.listing_plan_code == PlanCode.UNLIMITED
                        or is_company_downloaded
                    ):
                        corporate_numbers_downloaded = item.target_ids
                    else:
                        with Elasticsearch(
                            hosts=[es_url], http_auth=es_basic_auth, timeout=60
                        ) as elasticsearch:
                            es_client = elasticsearch
                            user = db.exec(
                                select(User).where(
                                    User.team_id == sync_log_history.team_id
                                )
                            ).first()
                            corporate_numbers_downloaded = download_companies(
                                db=db,
                                es_client=es_client,
                                current_user=UserBase(
                                    id=user.id,
                                    team_id=user.team_id,
                                    email=user.email,
                                    name=user.name,
                                ),
                                corporate_numbers=item.target_ids or [],
                            )

                    if len(corporate_numbers_downloaded) > 0:
                        hubspot_company_id = create_hubspot_company(
                            db=db,
                            sync_log_history=sync_log_history,
                            ss_company_corporate_number=item.target_ids[0],
                        )

                        client.update_person_association_id(
                            item.source_id, hubspot_company_id
                        )

                        synced_company = HubspotSyncedCompanies()
                        synced_company.ss_company_id = item.target_ids[0]
                        synced_company.hubspot_company_id = hubspot_company_id
                        synced_company.integration_id = sync_log_history.integration_id
                        synced_company.hubspot_team_id = (
                            sync_log_history.hubspot_team_id
                        )
                        ret.append(synced_company)

                        pull_history.error_type = None
                        pull_history.deleted_at = datetime.now()
                        db.add(pull_history)
                        db.flush()
                        db.refresh(pull_history)
                else:
                    not_found_hubspot_company = (
                        HubspotPersonNotFoundHubspotCompanyHistories()
                    )
                    not_found_hubspot_company.hubspot_person_log_id = pull_history.id
                    not_found_hubspot_company.ss_company_id = item.target_ids[0]
                    pull_history.error_type = "NOT_COMPANY"
                    ret.append(not_found_hubspot_company)
            else:
                """check if company exists in HubSpot"""
                try:
                    client.get_company_by_id(synced_company.hubspot_company_id)
                except HTTPException as e:
                    synced_company.deleted_at = datetime.now()
                    db.add(synced_company)
                    db.commit()
                    raise e

                sync_company_data_to_husbpot(
                    db=db,
                    log_id=sync_log_history.log_id,
                    ss_company_id=item.target_ids[0],
                    hubspot_company_id=synced_company.hubspot_company_id,
                )
                client.update_person_association_id(
                    item.source_id, synced_company.hubspot_company_id
                )

        db.add_all(ret)
        db.commit()
    except HTTPException as e:
        db.rollback()
        print("_______ error func handle_pull_person_item _______", str(e))
        raise e


def handle_pull_item(
    db: Session, item: IdentifyResult, sync_log_history: HubspotCompanySyncHistories
):
    print("_______ start func handle_pull_item _______")
    try:
        print("HANDLE PULL ITEM")
        print("---------- item -----------", item)
        ret = []
        pull_history = HubspotCompanyPullHistories()
        pull_history.log_id = sync_log_history.log_id
        pull_history.hubspot_company_id = item.source_id
        db.add(pull_history)
        db.flush()
        if len(item.target_ids) == 0:
            pull_history.error_type = "NOT_FOUND"
            not_found_history = HubspotCompanyNotFoundPullHistories()
            not_found_history.hubspot_pull_log_id = pull_history.id
            not_found_history.status = 0
            ret.append(not_found_history)
        if len(item.target_ids) > 1:
            pull_history.error_type = "MULTIPLE"
            multiple_history = HubspotCompanyMultiplePullHistories()
            multiple_history.hubspot_pull_log_id = pull_history.id
            multiple_history.matched_company_ids = item.target_ids
            multiple_history.status = 0
            ret.append(multiple_history)
        if len(item.target_ids) == 1:
            synced_company_detail = db.exec(
                select(HubspotSyncedCompanies).where(
                    HubspotSyncedCompanies.integration_id
                    == sync_log_history.integration_id,
                    HubspotSyncedCompanies.hubspot_team_id
                    == sync_log_history.hubspot_team_id,
                    HubspotSyncedCompanies.deleted_at.is_(None),
                    HubspotSyncedCompanies.ss_company_id == item.target_ids[0],
                )
            ).first()

            if synced_company_detail:
                pull_history.error_type = "NOT_FOUND"
                not_found_history = HubspotCompanyNotFoundPullHistories()
                not_found_history.hubspot_pull_log_id = pull_history.id
                not_found_history.status = 0
                ret.append(not_found_history)
            else:
                team = db.exec(
                    select(Team).where(Team.id == sync_log_history.team_id)
                ).one()
                if team:
                    is_company_downloaded = db.exec(
                        select(TeamCompany).where(
                            TeamCompany.corporate_number == item.target_ids[0],
                            TeamCompany.team_id == sync_log_history.team_id,
                            TeamCompany.deleted_at.is_(None),
                        )
                    ).first()
                    corporate_numbers_downloaded = []
                    if (
                        team.form_plan_code == PlanCode.UNLIMITED
                        or team.listing_plan_code == PlanCode.UNLIMITED
                        or is_company_downloaded
                    ):
                        corporate_numbers_downloaded = item.target_ids
                    else:
                        with Elasticsearch(
                            hosts=[es_url], http_auth=es_basic_auth, timeout=60
                        ) as elasticsearch:
                            es_client = elasticsearch
                            user = db.exec(
                                select(User).where(
                                    User.team_id == sync_log_history.team_id
                                )
                            ).first()
                            corporate_numbers_downloaded = download_companies(
                                db=db,
                                es_client=es_client,
                                current_user=UserBase(
                                    id=user.id,
                                    team_id=user.team_id,
                                    email=user.email,
                                    name=user.name,
                                ),
                                corporate_numbers=item.target_ids or [],
                            )
                    if len(corporate_numbers_downloaded) > 0:
                        pull_history.error_type = None
                        synced_company = HubspotSyncedCompanies()
                        synced_company.hubspot_company_id = item.source_id
                        synced_company.ss_company_id = item.target_ids[0]
                        synced_company.integration_id = sync_log_history.integration_id
                        synced_company.hubspot_team_id = (
                            sync_log_history.hubspot_team_id
                        )

                        sync_company_data_to_husbpot(
                            db=db,
                            log_id=sync_log_history.log_id,
                            ss_company_id=item.target_ids[0],
                            hubspot_company_id=item.source_id,
                        )
                        ret.append(synced_company)
        db.add_all(ret)
        db.commit()
    except HTTPException as e:
        db.rollback()
        print("_______ error func handle_pull_item _______", str(e))
        raise e


def handle_push_item(
    db: Session, item: IdentifyResult, sync_log_history: HubspotCompanySyncHistories
):
    print("_______ start func handle_push_item _______")
    try:
        print("HANDLE PUSH ITEM")
        print("---------- item -----------", item)
        ret = []
        push_history = HubspotCompanyPushHistories()
        push_history.log_id = sync_log_history.log_id
        push_history.ss_company_id = item.source_id
        db.add(push_history)
        db.flush()
        db.refresh(push_history)
        if len(item.target_ids) == 0:
            push_history.error_type = None
            hubspot_company_id = create_hubspot_company(
                db=db,
                sync_log_history=sync_log_history,
                ss_company_corporate_number=item.source_id,
            )
            synced_company = HubspotSyncedCompanies()
            synced_company.ss_company_id = item.source_id
            synced_company.hubspot_company_id = hubspot_company_id
            synced_company.integration_id = sync_log_history.integration_id
            synced_company.hubspot_team_id = sync_log_history.hubspot_team_id
            ret.append(synced_company)

            push_history.error_type = None
            push_history.deleted_at = datetime.now()
            db.add(push_history)
            db.flush()
            db.refresh(push_history)
        if len(item.target_ids) > 1:
            push_history.error_type = "MULTIPLE"
            multiple_history = HubspotCompanyMultiplePushHistories()
            multiple_history.hubspot_push_log_id = push_history.id
            multiple_history.matched_company_ids = item.target_ids
            multiple_history.status = 0
            ret.append(multiple_history)
        if len(item.target_ids) == 1:
            synced_company_detail = db.exec(
                select(HubspotSyncedCompanies).where(
                    HubspotSyncedCompanies.integration_id
                    == sync_log_history.integration_id,
                    HubspotSyncedCompanies.hubspot_team_id
                    == sync_log_history.hubspot_team_id,
                    HubspotSyncedCompanies.deleted_at.is_(None),
                    HubspotSyncedCompanies.hubspot_company_id == item.target_ids[0],
                )
            ).first()
            if synced_company_detail:
                push_history.error_type = "NOT_FOUND"
                not_found_history = HubspotCompanyNotFoundPushHistories()
                not_found_history.hubspot_push_log_id = push_history.id
                not_found_history.status = 0
                ret.append(not_found_history)
            else:
                push_history.error_type = None
                synced_company = HubspotSyncedCompanies()
                synced_company.ss_company_id = item.source_id
                synced_company.hubspot_company_id = item.target_ids[0]
                synced_company.integration_id = sync_log_history.integration_id
                synced_company.hubspot_team_id = sync_log_history.hubspot_team_id
                sync_company_data_to_husbpot(
                    db=db,
                    log_id=sync_log_history.log_id,
                    ss_company_id=item.source_id,
                    hubspot_company_id=item.target_ids[0],
                )
                ret.append(synced_company)
        db.add_all(ret)
        db.commit()
    except HTTPException as e:
        db.rollback()
        print("_______ error func handle_push_item _______", str(e.detail))
        raise e


def handle_salesforce_push_company(
    db: Session,
    item: SalesforceIdentifyResult,
    sync_log_history: SalesforceSyncHistories,
):
    print("_______ start func handle_salesforce_push_company _______")
    try:
        print("HANDLE SALESFORCE PUSH ITEM")
        print("---------- item -----------", item)
        ret = []
        push_history = SalesforceCompanyPushHistories()
        push_history.log_id = sync_log_history.log_id
        push_history.ss_company_id = item.source_id
        push_history.salesforce_team_id = sync_log_history.salesforce_team_id
        push_history.salesforce_integration_id = (
            sync_log_history.salesforce_integration_id
        )
        push_history.team_id = sync_log_history.team_id
        db.add(push_history)
        db.flush()
        db.refresh(push_history)
        if len(item.target_ids) == 0:
            push_history.error_type = None
            salesforce_company_id = create_salesforce_company(
                db=db,
                sync_log_history=sync_log_history,
                ss_company_corporate_number=item.source_id,
            )
            synced_company = SalesforceSyncedCompanies()
            synced_company.ss_company_id = item.source_id
            synced_company.salesforce_company_id = salesforce_company_id
            synced_company.salesforce_integration_id = (
                sync_log_history.salesforce_integration_id
            )
            synced_company.salesforce_team_id = sync_log_history.salesforce_team_id
            ret.append(synced_company)

            push_history.error_type = None
            push_history.deleted_at = datetime.now()
            db.add(push_history)
            db.flush()
            db.refresh(push_history)
        if len(item.target_ids) > 1:
            push_history.error_type = "MULTIPLE"
            multiple_history = SalesforceCompanyMultiplePushHistories()
            multiple_history.salesforce_push_history_id = push_history.id
            multiple_history.matched_company_ids = item.target_ids
            multiple_history.status = 0
            ret.append(multiple_history)
        if len(item.target_ids) == 1:
            synced_company_detail = db.exec(
                select(SalesforceSyncedCompanies).where(
                    SalesforceSyncedCompanies.salesforce_integration_id
                    == sync_log_history.salesforce_integration_id,
                    SalesforceSyncedCompanies.salesforce_team_id
                    == sync_log_history.salesforce_team_id,
                    SalesforceSyncedCompanies.deleted_at.is_(None),
                    SalesforceSyncedCompanies.salesforce_company_id
                    == item.target_ids[0],
                )
            ).first()
            if synced_company_detail:
                push_history.error_type = "NOT_FOUND"
                not_found_history = SalesforceCompanyNotFoundPushHistories()
                not_found_history.salesforce_push_history_id = push_history.id
                not_found_history.status = 0
                ret.append(not_found_history)
            else:
                push_history.error_type = None
                synced_company = SalesforceSyncedCompanies()
                synced_company.ss_company_id = item.source_id
                synced_company.salesforce_company_id = item.target_ids[0]
                synced_company.salesforce_integration_id = (
                    sync_log_history.salesforce_integration_id
                )
                synced_company.salesforce_team_id = sync_log_history.salesforce_team_id
                sync_company_data_to_salesforce(
                    db=db,
                    log_id=sync_log_history.log_id,
                    ss_company_id=item.source_id,
                    salesforce_company_id=item.target_ids[0],
                )
                ret.append(synced_company)
        db.add_all(ret)
        db.commit()
    except HTTPException as e:
        db.rollback()
        print("_______ error func handle_salesforce_push_company _______", str(e))
        raise e


def handle_salesforce_pull_company(
    db: Session,
    item: SalesforceIdentifyResult,
    sync_log_history: SalesforceSyncHistories,
):
    print("_______ start func handle_salesforce_pull_company _______")
    try:
        print("HANDLE SALESFORCE PULL ITEM")
        print("---------- SALESFORCE item -----------", item)
        ret = []
        pull_history = SalesforceCompanyPullHistories()
        pull_history.log_id = sync_log_history.log_id
        pull_history.salesforce_company_id = item.source_id
        pull_history.salesforce_team_id = sync_log_history.salesforce_team_id
        pull_history.salesforce_integration_id = (
            sync_log_history.salesforce_integration_id
        )
        pull_history.team_id = sync_log_history.team_id
        db.add(pull_history)
        db.flush()
        if len(item.target_ids) == 0:
            pull_history.error_type = "NOT_FOUND"
            not_found_history = SalesforceCompanyNotFoundPullHistories()
            not_found_history.salesforce_pull_history_id = pull_history.id
            not_found_history.status = 0
            ret.append(not_found_history)
        if len(item.target_ids) > 1:
            pull_history.error_type = "MULTIPLE"
            multiple_history = SalesforceCompanyMultiplePullHistories()
            multiple_history.salesforce_pull_history_id = pull_history.id
            multiple_history.matched_company_ids = item.target_ids
            multiple_history.status = 0
            ret.append(multiple_history)
        if len(item.target_ids) == 1:
            synced_company_detail = db.exec(
                select(SalesforceSyncedCompanies).where(
                    SalesforceSyncedCompanies.salesforce_integration_id
                    == sync_log_history.salesforce_integration_id,
                    SalesforceSyncedCompanies.salesforce_team_id
                    == sync_log_history.salesforce_team_id,
                    SalesforceSyncedCompanies.deleted_at.is_(None),
                    SalesforceSyncedCompanies.ss_company_id == item.target_ids[0],
                )
            ).first()
            if synced_company_detail:
                pull_history.error_type = "NOT_FOUND"
                not_found_history = SalesforceCompanyNotFoundPullHistories()
                not_found_history.salesforce_pull_history_id = pull_history.id
                not_found_history.status = 0
                ret.append(not_found_history)
            else:
                team = db.exec(
                    select(Team).where(Team.id == sync_log_history.team_id)
                ).one()
                if team:
                    is_company_downloaded = db.exec(
                        select(TeamCompany).where(
                            TeamCompany.corporate_number == item.target_ids[0],
                            TeamCompany.team_id == sync_log_history.team_id,
                            TeamCompany.deleted_at.is_(None),
                        )
                    ).first()
                    corporate_numbers_downloaded = []
                    if (
                        team.form_plan_code == PlanCode.UNLIMITED
                        or team.listing_plan_code == PlanCode.UNLIMITED
                        or is_company_downloaded
                    ):
                        corporate_numbers_downloaded = item.target_ids
                    else:
                        with Elasticsearch(
                            hosts=[es_url], http_auth=es_basic_auth, timeout=60
                        ) as elasticsearch:
                            es_client = elasticsearch
                            user = db.exec(
                                select(User).where(
                                    User.team_id == sync_log_history.team_id
                                )
                            ).first()
                            corporate_numbers_downloaded = download_companies(
                                db=db,
                                es_client=es_client,
                                current_user=UserBase(
                                    id=user.id,
                                    team_id=user.team_id,
                                    email=user.email,
                                    name=user.name,
                                ),
                                corporate_numbers=item.target_ids or [],
                            )
                    if len(corporate_numbers_downloaded) > 0:
                        pull_history.error_type = None
                        synced_company = SalesforceSyncedCompanies()
                        synced_company.salesforce_company_id = item.source_id
                        synced_company.ss_company_id = item.target_ids[0]
                        synced_company.salesforce_integration_id = (
                            sync_log_history.salesforce_integration_id
                        )
                        synced_company.salesforce_team_id = (
                            sync_log_history.salesforce_team_id
                        )

                        sync_company_data_to_salesforce(
                            db=db,
                            log_id=sync_log_history.log_id,
                            ss_company_id=item.target_ids[0],
                            salesforce_company_id=item.source_id,
                        )
                        ret.append(synced_company)
        db.add_all(ret)
        db.commit()
    except HTTPException as e:
        db.rollback()
        print("_______ error func handle_salesforce_pull_company _______", str(e))
        raise e


def handle_salesforce_pull_person(
    db: Session,
    item: SalesforceIdentifyResult,
    sync_log_history: SalesforceSyncHistories,
):
    print("_______ start func handle_salesforce_pull_person _______")
    try:
        print("HANDLE PULL PERSON ITEM")
        print("---------- item -----------", item)
        ret = []
        pull_history = SalesforcePersonPullHistories()
        pull_history.log_id = sync_log_history.log_id
        pull_history.salesforce_person_id = item.source_id
        db.add(pull_history)
        db.flush()
        if len(item.target_ids) == 0:
            pull_history.error_type = "NOT_FOUND"
            not_found_history = SalesforcePersonNotFoundPullHistories()
            not_found_history.salesforce_person_history_id = pull_history.id
            ret.append(not_found_history)
        if len(item.target_ids) > 1:
            pull_history.error_type = "MULTIPLE"
            multiple_history = SalesforcePersonMultiplePullHistories()
            multiple_history.salesforce_person_history_id = pull_history.id
            multiple_history.matched_company_ids = item.target_ids
            ret.append(multiple_history)
        if len(item.target_ids) == 1:
            pull_history.error_type = None
            synced_company = db.exec(
                select(SalesforceSyncedCompanies).where(
                    SalesforceSyncedCompanies.ss_company_id == item.target_ids[0],
                    SalesforceSyncedCompanies.salesforce_integration_id
                    == sync_log_history.salesforce_integration_id,
                    SalesforceSyncedCompanies.salesforce_team_id
                    == sync_log_history.salesforce_team_id,
                    SalesforceSyncedCompanies.deleted_at.is_(None),
                )
            ).first()
            sf_integration = db.exec(
                select(SalesforceIntegrations).where(
                    SalesforceIntegrations.id
                    == sync_log_history.salesforce_integration_id,
                    SalesforceIntegrations.deleted_at.is_(None),
                )
            ).first()

            salesforce_service = SalesforceService(
                access_token=sf_integration.access_token,
                refresh_token=sf_integration.refresh_token,
                instance_url=sf_integration.instance_url,
                id_url=sf_integration.id_url,
            )

            if not synced_company:
                team = db.exec(
                    select(Team).where(Team.id == sync_log_history.team_id)
                ).one()
                if team:
                    is_company_downloaded = db.exec(
                        select(TeamCompany).where(
                            TeamCompany.corporate_number == item.target_ids[0],
                            TeamCompany.team_id == sync_log_history.team_id,
                            TeamCompany.deleted_at.is_(None),
                        )
                    ).first()
                    corporate_numbers_downloaded = []
                    if (
                        team.form_plan_code == PlanCode.UNLIMITED
                        or team.listing_plan_code == PlanCode.UNLIMITED
                        or is_company_downloaded
                    ):
                        corporate_numbers_downloaded = item.target_ids
                    else:
                        with Elasticsearch(
                            hosts=[es_url], http_auth=es_basic_auth, timeout=60
                        ) as elasticsearch:
                            es_client = elasticsearch
                            user = db.exec(
                                select(User).where(
                                    User.team_id == sync_log_history.team_id
                                )
                            ).first()
                            corporate_numbers_downloaded = download_companies(
                                db=db,
                                es_client=es_client,
                                current_user=UserBase(
                                    id=user.id,
                                    team_id=user.team_id,
                                    email=user.email,
                                    name=user.name,
                                ),
                                corporate_numbers=item.target_ids or [],
                            )
                    if len(corporate_numbers_downloaded) > 0:
                        salesforce_company_id = create_salesforce_company(
                            db=db,
                            sync_log_history=sync_log_history,
                            ss_company_corporate_number=item.target_ids[0],
                        )

                        salesforce_service.update_person_account_id(
                            person_id=item.source_id,
                            account_id=salesforce_company_id,
                        )

                        synced_company = SalesforceSyncedCompanies()
                        synced_company.ss_company_id = item.target_ids[0]
                        synced_company.salesforce_company_id = salesforce_company_id
                        synced_company.salesforce_integration_id = (
                            sync_log_history.salesforce_integration_id
                        )
                        synced_company.salesforce_team_id = (
                            sync_log_history.salesforce_team_id
                        )
                        ret.append(synced_company)

                        pull_history.error_type = None
                        pull_history.deleted_at = datetime.now()
                        db.add(pull_history)
                        db.flush()
                        db.refresh(pull_history)
                else:
                    not_found_hubspot_company = SalesforcePersonNotFoundPullHistories()
                    not_found_hubspot_company.salesforce_person_history_id = (
                        pull_history.id
                    )
                    pull_history.error_type = "NOT_COMPANY"
                    ret.append(not_found_hubspot_company)
            else:
                """check if company exists in HubSpot"""
                try:
                    salesforce_service.get_company_by_id(
                        synced_company.salesforce_company_id
                    )
                except HTTPException as e:
                    synced_company.deleted_at = datetime.now()
                    db.add(synced_company)
                    db.commit()
                    raise e

                sync_company_data_to_salesforce(
                    db=db,
                    log_id=sync_log_history.log_id,
                    ss_company_id=item.target_ids[0],
                    salesforce_company_id=synced_company.salesforce_company_id,
                )

                if sf_integration:
                    salesforce_service.update_person_account_id(
                        person_id=item.source_id,
                        account_id=synced_company.salesforce_company_id,
                    )

        db.add_all(ret)
        db.commit()
    except HTTPException as e:
        db.rollback()
        print("_______ error func handle_salesforce_pull_person _______", str(e))
        raise e


IDENTIFY_ACTION_HANDLER = {
    IdentifyAction.PULL: handle_pull_item,
    IdentifyAction.PUSH: handle_push_item,
    IdentifyAction.PULL_PERSON: handle_pull_person_item,
    TYPE_INTEGRATION_ENUM.PUSH_COMPANIES: handle_salesforce_push_company,
    TYPE_INTEGRATION_ENUM.PULL_COMPANIES: handle_salesforce_pull_company,
    TYPE_INTEGRATION_ENUM.PULL_PERSONS: handle_salesforce_pull_person,
}


def download_companies(
    db: Session, es_client, current_user: UserBase, corporate_numbers: List[str]
):
    if len(corporate_numbers) > 10000:
        raise BadRequestException(detail="company.tooManyCompanies")
    team = db.exec(select(Team).where(Team.id == current_user.team_id)).one()

    if team.listing_plan_code == PlanCode.UNLIMITED:
        raise ConflictException(detail="company.companyHasAlreadyDownloaded")

    corporate_numbers_downloaded = (
        db.execute(
            sqlalchemy.select(TeamCompany.corporate_number)
            .where(col(TeamCompany.corporate_number).in_(corporate_numbers))
            .where(TeamCompany.team_id == current_user.team_id)
        )
        .scalars()
        .all()
    )
    corporate_numbers_will_download = [
        x for x in corporate_numbers if x not in corporate_numbers_downloaded
    ]

    amount_will_spend = settings.AMOUNT_PER_DOWNLOAD * len(
        corporate_numbers_will_download
    )

    if not is_enough_credit(db, current_user.team_id, amount_will_spend):
        raise PaymentRequiredException(
            detail={
                "message": "company.notEnoughCredit",
                "remaining_credit": remaining_credit(db, current_user.team_id),
            }
        )

    try:
        team_companies = [
            TeamCompany(
                team_id=current_user.team_id,
                corporate_number=x,
                status_code=StatusCode.PENDING,
            )
            for x in corporate_numbers_will_download
        ]
        db.bulk_save_objects(team_companies)
        db.flush()

        downloaded_histories = DownloadedHistory(
            user_id=current_user.id,
            amount=amount_will_spend,
            service_code=ServiceCode.CPN,
        )
        db.add(downloaded_histories)
        db.commit()
        consume_credit(
            db,
            current_user.team_id,
            amount_will_spend,
            service_code=ServiceCode.CPN,
        )

        if len(corporate_numbers_will_download) > 0:
            ubq = UpdateByQuery(using=es_client, index=EsCompanyExtend.Index.name)
            update_query = Q("terms", corporate_number=corporate_numbers_will_download)
            ubq = ubq.query(update_query).script(
                source="""
                if(ctx._source.team_ids==null) ctx._source.team_ids = [params.team_id];
                else ctx._source.team_ids.add(params.team_id);
                """,
                lang="painless",
                params={"team_id": current_user.team_id},
            )
            ubq.params(refresh="wait_for")
            ubq.params(retry_on_conflict=3)
            try:
                ubq.execute()
            except ConflictError:
                pass

    except HTTPException as e:
        db.rollback()
        raise e

    return corporate_numbers_will_download
