from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from app.models.integration.salesforce.salesforce_sync_histories import (
    TYPE_INTEGRATION_ENUM,
)


class SSCompany(BaseModel):
    corporate_number: str
    name: Optional[str]
    domain: Optional[str]


class HubspotCompany(BaseModel):
    id: str
    name: Optional[str]
    domain: Optional[str]


class HubspotPerson(BaseModel):
    id: str
    email: str
    domain: Optional[str]


class IdentifyAction(str, Enum):
    PULL = "PULL"
    PUSH = "PUSH"
    PULL_PERSON = "PULL_PERSON"
    SYNC_COMPANIES = "SYNC_COMPANIES"
    PULL_COMPANIES = "PULL_COMPANIES"
    PUSH_COMPANIES = "PUSH_COMPANIES"
    PULL_PERSONS = "PULL_PERSONS"


class IdentifyResult(BaseModel):
    source_id: str  # pull: hubspot_id / push: ss_id
    target_ids: List[str]
    action: IdentifyAction


class SalesforceIdentifyResult(BaseModel):
    source_id: str  # pull: salesforce_id / push: ss_id
    target_ids: List[str]
    action: TYPE_INTEGRATION_ENUM


class SalesforceCompany(BaseModel):
    id: str
    name: Optional[str]
    domain: Optional[str]


class SalesforcePerson(BaseModel):
    id: str
    email: str
    domain: Optional[str]
