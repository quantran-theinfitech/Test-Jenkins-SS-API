from datetime import datetime
from typing import List

from fastapi import HTTPException
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.constant.constants import INTEGRATION_PLATFORM_ENUM
from app.db import engine
from app.models.integration.hubspot.hubspot_company_sync_histories import (
    HubspotCompanySyncHistories,
)
from app.models.integration.hubspot.hubspot_pull_person_histories import (
    HubspotPullPersonHistories,
)
from app.models.integration.hubspot.hubspot_raw_persons import HubspotRawPersons
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from app.models.integration.salesforce.salesforce_person_pull_histories import (
    SalesforcePersonPullHistories,
)
from app.models.integration.salesforce.salesforce_raw_persons import (
    SalesforceRawPersons,
)
from app.models.integration.salesforce.salesforce_sync_histories import (
    SalesforceSyncHistories,
)
from utils.hubspot_connection import HubSpotService
from utils.identify.schema import (
    HubspotPerson,
    IdentifyAction,
    IdentifyResult,
    SalesforcePerson,
)
from utils.identify.utils import (
    extract_domain,
    get_intergration,
    query_matched_companies,
)
from utils.integration.salesforce import SalesforceService

identify_patterns = [["domain"]]
skip_domains = [
    "gmail.com",
    "yahoo.com",
    "yahoo.co.jp",
    "docomo.ne.jp",
    "ezweb.ne.jp",
    "softbank.ne.jp",
    "i.softbank.jp",
    "outlook.jp",
    "outlook.com",
    "hotmail.com",
    "hotmail.co.jp",
    "me.com",
    "icloud.com",
]


def match_company_pull_persons(db, hubspot_person: HubspotPerson):
    print("_______ start func match_company_pull_persons _______")
    try:
        matched_companies = query_matched_companies(
            db, "", hubspot_person.domain if hubspot_person.domain is not None else ""
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
                    if not hubspot_person.__dict__[col]:
                        match_flag = False
                        break
                    if matched_company.__dict__[col] != hubspot_person.__dict__[col]:
                        match_flag = False
                        break
                if match_flag:
                    result.append(matched_company.corporate_number)
            if result:
                break
        return result
    except HTTPException as e:
        print("_______ error of func match_company_pull_persons _______", str(e))
        raise e


def pull_person_identify(
    integration_id: int,
    platform: str = INTEGRATION_PLATFORM_ENUM["HUBSPOT"],
) -> List[IdentifyResult]:
    print("_______ start func pull_person_identify _______")
    print("_______ platform _______", platform)
    try:
        with Session(engine) as db:
            result = []
            if platform == INTEGRATION_PLATFORM_ENUM["HUBSPOT"]:
                hubspot_integration = get_intergration(
                    db, integration_id=integration_id, platform=platform
                )
                access_token, refresh_token = (
                    hubspot_integration.access_token,
                    hubspot_integration.refresh_token,
                )
                client = HubSpotService(
                    access_token=access_token, refresh_token=refresh_token
                )

                hubspot_persons = []
                hubspot_raw_persons = []

                no_company_persons = client.get_nocompany_contacts()

                if no_company_persons and len(no_company_persons) > 0:
                    for person in no_company_persons:
                        person_marked_done = db.exec(
                            select(HubspotPullPersonHistories)
                            .join(
                                HubspotCompanySyncHistories,
                                HubspotCompanySyncHistories.log_id
                                == HubspotPullPersonHistories.log_id,
                            )
                            .where(
                                HubspotPullPersonHistories.hubspot_person_id
                                == person.id,
                                HubspotCompanySyncHistories.integration_id
                                == integration_id,
                                HubspotPullPersonHistories.deleted_at.isnot(None),
                                HubspotPullPersonHistories.error_type.isnot(None),
                            )
                        ).first()

                        if person_marked_done:
                            continue
                        elif (
                            person.properties.get("email")
                            and extract_domain(person.properties.get("email"))
                            not in skip_domains
                        ):
                            hubspot_persons.append(
                                HubspotPerson(
                                    id=person.id,
                                    email=person.properties.get("email"),
                                    domain=extract_domain(
                                        person.properties.get("email")
                                    ),
                                )
                            )
                            hubspot_raw_persons.append(
                                HubspotRawPersons(
                                    hubspot_person_id=person.id,
                                    integration_id=integration_id,
                                    hubspot_team_id=hubspot_integration.hubspot_team_id,
                                    data=person.properties,
                                ).dict()
                            )

                hubspot_raw_persons_dicts = [
                    {k: v for k, v in company.items() if k != "id"}
                    for company in hubspot_raw_persons
                ]
                stmt = insert(HubspotRawPersons).values(hubspot_raw_persons_dicts)

                stmt = stmt.on_conflict_do_update(
                    constraint="hubspot_raw_persons_unique_key",
                    set_={
                        x.name: getattr(stmt.excluded, x.name)
                        for x in HubspotRawPersons.metadata.tables[
                            "hubspot_raw_persons"
                        ].columns
                        if x.name != "id"
                    },
                )

                db.execute(stmt)

                pull_person_history = db.exec(
                    select(HubspotPullPersonHistories)
                    .join(
                        HubspotCompanySyncHistories,
                        HubspotCompanySyncHistories.log_id
                        == HubspotPullPersonHistories.log_id,
                    )
                    .where(
                        HubspotCompanySyncHistories.integration_id == integration_id,
                        HubspotPullPersonHistories.deleted_at.is_(None),
                    )
                ).fetchall()

                hubspot_person_ids = []
                if len(hubspot_persons) > 0:
                    hubspot_person_ids = [
                        hubspot_person.id for hubspot_person in hubspot_persons
                    ]
                if pull_person_history and len(pull_person_history) > 0:
                    for pull_person in pull_person_history:
                        if pull_person.hubspot_person_id not in hubspot_person_ids:
                            pull_person.deleted_at = datetime.now()
                            db.add(pull_person)

                db.commit()

                for hubspot_person in hubspot_persons:
                    result.append(
                        IdentifyResult(
                            source_id=hubspot_person.id,
                            target_ids=match_company_pull_persons(db, hubspot_person),
                            action=IdentifyAction.PULL_PERSON,
                        )
                    )

            if platform == INTEGRATION_PLATFORM_ENUM["SALESFORCE"]:
                sf_connection = db.exec(
                    select(SalesforceIntegrations).where(
                        SalesforceIntegrations.id == integration_id,
                        SalesforceIntegrations.deleted_at.is_(None),
                    )
                ).first()

                salesforce_client = SalesforceService(
                    access_token=sf_connection.access_token,
                    refresh_token=sf_connection.refresh_token,
                    instance_url=sf_connection.instance_url,
                    id_url=sf_connection.id_url,
                )

                salesforce_persons = []
                salesforce_raw_persons = []

                nocompany_persons = salesforce_client.get_nocompany_persons()

                if nocompany_persons and len(nocompany_persons) > 0:
                    for person in nocompany_persons:
                        person_marked_done = db.exec(
                            select(SalesforcePersonPullHistories)
                            .join(
                                SalesforceSyncHistories,
                                SalesforceSyncHistories.log_id
                                == SalesforcePersonPullHistories.log_id,
                            )
                            .where(
                                SalesforcePersonPullHistories.salesforce_person_id
                                == person["Id"],
                                SalesforceSyncHistories.salesforce_integration_id
                                == integration_id,
                                SalesforcePersonPullHistories.deleted_at.isnot(None),
                                SalesforcePersonPullHistories.error_type.isnot(None),
                            )
                        ).first()

                        if person_marked_done:
                            continue
                        elif (
                            person["Email"]
                            and extract_domain(person["Email"]) not in skip_domains
                        ):
                            salesforce_persons.append(
                                SalesforcePerson(
                                    id=person["Id"],
                                    email=person["Email"],
                                    domain=extract_domain(person["Email"]),
                                )
                            )
                            salesforce_raw_persons.append(
                                SalesforceRawPersons(
                                    salesforce_team_id=sf_connection.salesforce_team_id,
                                    salesforce_person_id=person["Id"],
                                    salesforce_integration_id=integration_id,
                                    data=person,
                                ).dict()
                            )

                if salesforce_raw_persons and len(salesforce_raw_persons) > 0:
                    salesforce_raw_persons_dicts = [
                        {k: v for k, v in person.items() if k != "id"}
                        for person in salesforce_raw_persons
                    ]
                    stmt = insert(SalesforceRawPersons).values(
                        salesforce_raw_persons_dicts
                    )

                    stmt = stmt.on_conflict_do_update(
                        constraint="salesforce_raw_persons_unique_key",
                        set_={
                            x.name: getattr(stmt.excluded, x.name)
                            for x in SalesforceRawPersons.metadata.tables[
                                "salesforce_raw_persons"
                            ].columns
                            if x.name != "id"
                        },
                    )

                    db.execute(stmt)

                pull_person_history = db.exec(
                    select(SalesforcePersonPullHistories)
                    .join(
                        SalesforceSyncHistories,
                        SalesforceSyncHistories.log_id
                        == SalesforcePersonPullHistories.log_id,
                    )
                    .where(
                        SalesforceSyncHistories.salesforce_integration_id
                        == integration_id,
                        SalesforcePersonPullHistories.deleted_at.is_(None),
                        SalesforceSyncHistories.deleted_at.is_(None),
                    )
                ).fetchall()

                salesforce_person_ids = []
                if len(salesforce_persons) > 0:
                    salesforce_person_ids = [
                        salesforce_person.id for salesforce_person in salesforce_persons
                    ]
                if pull_person_history and len(pull_person_history) > 0:
                    for pull_person in pull_person_history:
                        if (
                            pull_person.salesforce_person_id
                            not in salesforce_person_ids
                        ):
                            pull_person.deleted_at = datetime.now()
                            db.add(pull_person)

                db.commit()

                for salesforce_person in salesforce_persons:
                    result.append(
                        IdentifyResult(
                            source_id=salesforce_person.id,
                            target_ids=match_company_pull_persons(
                                db, salesforce_person
                            ),
                            action=IdentifyAction.PULL_PERSONS,
                        )
                    )

            return result
    except HTTPException as e:
        print("_______ error of func pull_person_identify _______", str(e))
        db.rollback()
        raise e
    finally:
        print("_______ end func pull_person_identify _______")
