from typing import List, Optional, Union

import requests
from fastapi import HTTPException
from simple_salesforce.api import Salesforce
from simple_salesforce.exceptions import SalesforceError
from sqlmodel import Session, select

from app.api.base.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.config import settings
from app.constant.constants import INDUSTRIES_CATEGORIES, LISTING_MARKET_CODE
from app.models.city import City
from app.models.company import Company
from app.models.integration.salesforce.salesforce_company_field_mappings import (
    SalesforceCompanyFieldMappings,
)
from app.models.integration.salesforce.salesforce_integrations import (
    SalesforceIntegrations,
)
from app.models.integration.salesforce.salesforce_sync_histories import (
    SalesforceSyncHistories,
)
from app.models.prefecture import Prefecture
from utils.extension import validate_and_clean_domain


class SalesforceService:
    def __init__(
        self, access_token, refresh_token=None, instance_url=None, id_url=None
    ):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.instance_url = instance_url
        self.id_url = id_url
        self.client = Salesforce(
            instance_url=self.instance_url, session_id=self.access_token, version="63.0"
        )

    def refresh_client(self):
        try:
            auth_data = {
                "grant_type": "refresh_token",
                "client_id": settings.SALESFORCE_CLIENT_ID,
                "client_secret": settings.SALESFORCE_CLIENT_SECRET,
                "refresh_token": self.refresh_token,
            }
            response = requests.post(settings.SALESFORCE_TOKEN_URL, data=auth_data)
            response_data = response.json()

            if response.status_code != 200 and response.status_code != 201:
                print("_______ error refresh_client _______", response_data)
                raise HTTPException(
                    status_code=response.status_code, detail=response_data
                )

            self.client = Salesforce(
                instance_url=self.instance_url,
                session_id=response_data["access_token"],
                version="63.0",
            )
        except HTTPException as e:
            print("_______ error refresh_client _______", str(e.detail))
            raise_exception_salesforce(e)

    def get_user_info(self):
        self.refresh_client()
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            response = requests.get(
                self.id_url if self.id_url else settings.SALESFORCE_USER_INFO_URL,
                headers=headers,
            )

            if response.status_code != 200 and response.status_code != 201:
                print("_______ error get_user_info _______", response.json())
                raise HTTPException(
                    status_code=response.status_code, detail=response.json()
                )

            user_info = response.json()
            return user_info
        except HTTPException as e:
            print("_______ error get_user_info _______", str(e))
            raise_exception_salesforce(e)

    def get_company_schema(self):
        self.refresh_client()
        try:
            company_schema = self.client.Account.describe()["fields"]
            if company_schema is None:
                return []

            return company_schema
        except SalesforceError as e:
            print("_______ error get_company_schema _______", str(e))
            raise_exception_salesforce(e)

    def get_all_companies(self, properties: Optional[List[str]] = None):
        self.refresh_client()
        try:
            if properties is not None and "Id" not in properties:
                properties.append("Id")
            query = f"""
                SELECT {', '.join(properties or ['Id', 'Name', 'Type', 'Website'])}
                FROM Account
                """
            response = self.client.query(query)

            return response["records"]
        except SalesforceError as e:
            print("_______ error get_all_companies _______", str(e))
            raise_exception_salesforce(e)

    def get_companies_by_ids(
        self, company_ids: List[str], properties: Optional[List[str]] = None
    ):
        self.refresh_client()
        try:
            if properties is not None and "Id" not in properties:
                properties.append("Id")
            query = f"""
                SELECT {', '.join(properties or ['Id', 'Name', 'Type', 'Website'])}
                FROM Account
                WHERE Id IN ({', '.join(f"'{cid}'" for cid in company_ids)})
                """
            response = self.client.query(query)
            if not response.get("records") or len(response["records"]) == 0:
                return []
            return response["records"]
        except SalesforceError as e:
            print("_______ error get_companies_by_ids _______", str(e))
            raise_exception_salesforce(e)

    def get_company_by_id(
        self, company_id: str, properties: Optional[List[str]] = None
    ):
        self.refresh_client()
        try:
            fields = ", ".join(properties or ["Id", "Name", "Type", "Website"])
            query = f"SELECT {fields} FROM Account WHERE Id = '{company_id}'"
            response = self.client.query(query)

            if not response.get("records") or len(response["records"]) == 0:
                raise NotFoundException(detail="integration.salesforce.companyNotFound")

            return response["records"][0]
        except SalesforceError as e:
            print("_______ error get_company_by_id _______", str(e))
            raise_exception_salesforce(e)

    def search_companies(
        self, search_string: str, properties: Optional[List[str]] = None
    ):
        self.refresh_client()
        try:
            if properties is not None and "Id" not in properties:
                properties.append("Id")
            query = f"""
                SELECT {', '.join(properties or ['Id', 'Name', 'Type', 'Website'])}
                FROM Account
                WHERE Name LIKE '%{search_string}%' OR Website LIKE '%{search_string}%'
                """
            response = self.client.query_all(query)
            return response["records"]
        except SalesforceError as e:
            print("_______ error search_companies _______", str(e))
            raise_exception_salesforce(e)

    def create_company(self, properties):
        self.refresh_client()
        try:
            response = self.client.Account.create(properties)
            return response
        except SalesforceError as e:
            print("_______ error create_company _______", str(e))
            raise_exception_salesforce(e)

    def update_company(self, company_id: str, properties):
        self.refresh_client()
        try:
            self.client.Account.update(record_id=company_id, data=properties)
        except SalesforceError as e:
            print("_______ error update_company _______", str(e))
            raise_exception_salesforce(e)

    def get_nocompany_persons(self):
        self.refresh_client()
        try:
            query = """
                SELECT Id, FirstName, LastName, Email
                FROM Contact
                WHERE AccountId = NULL
            """
            response = self.client.query_all(query)
            return response["records"]
        except SalesforceError as e:
            print("_______ error get_nocompany_persons _______", str(e))
            raise_exception_salesforce(e)

    def update_person_account_id(self, person_id: str, account_id: str):
        self.refresh_client()
        try:
            self.client.Contact.update(
                record_id=person_id, data={"AccountId": account_id}
            )
        except SalesforceError as e:
            print("_______ error update_person_account_id _______", str(e))
            raise_exception_salesforce(e)

    def create_custom_field(
        self, name: str, label: str, type: str = "Text", length: int = 255
    ):
        self.refresh_client()
        list_name_profile = [
            "System Administrator",
            "Standard User",
        ]

        list_id_profile = []
        for name_profile in list_name_profile:
            try:
                id_profile = self.get_id_profile(name_profile)
                if id_profile:
                    list_id_profile.append(id_profile)
            except HTTPException:
                continue

        list_id_permission_set = []
        for id_profile in list_id_profile:
            try:
                id_permission_set = self.get_id_permission_set(id_profile)
                if id_permission_set:
                    list_id_permission_set.append(id_permission_set)
            except HTTPException:
                continue

        try:
            # Metadata API endpoint for creating custom fields
            metadata_url = (
                f"{self.instance_url}/services/data/v63.0/tooling/sobjects/CustomField"
            )
            fullName = f"Account.{name}{'' if name.endswith('__c') else '__c'}"

            # Construct metadata for the custom field
            field_metadata = {
                "FullName": fullName,
                "Metadata": {
                    "fullName": fullName,
                    "type": type,  # Field type (e.g., Text, Number, etc.)
                    "label": label,  # Field label
                    "length": (
                        length if type == "Text" else None
                    ),  # Length for text fields
                    "precision": (
                        18 if type == "Number" else None
                    ),  # Precision for number fields
                    "scale": 0 if type == "Number" else None,  # Scale for number fields
                    "description": f"""
                        Custom field {name} created via Metadata API in SalesSmart
                    """,
                    "securityClassification": "Public",  # Security classification
                },
            }

            # Remove None values from the metadata
            field_metadata["Metadata"] = {
                k: v for k, v in field_metadata["Metadata"].items() if v is not None
            }

            # Set the headers, including the Authorization (Bearer token)
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            # Send POST request to create the custom field
            response = requests.post(metadata_url, headers=headers, json=field_metadata)

            # Check if the response is successful (status code 201 means Created)
            if response.status_code == 201:
                valid_permission_set_ids = [
                    pid for pid in list_id_permission_set if pid is not None
                ]
                self.update_field_level_security(
                    field_name=fullName,
                    permission_set_ids=valid_permission_set_ids,
                )
            else:
                print(f"Failed to create custom field: {response.status_code}")
                print(response.json())
                raise HTTPException(status_code=400, detail=response.json())

        except HTTPException as e:
            print("_______ error create_custom_field _______", str(e.detail))
            raise_exception_salesforce(e)

    def get_id_profile(self, name_profile: str):
        self.refresh_client()
        try:
            # Metadata API endpoint for querying Profile
            query = f"SELECT Id FROM Profile WHERE Name='{name_profile}'"
            resp = self.client.query(query)
            if not resp.get("records") or len(resp["records"]) == 0:
                return None
            return resp["records"][0]["Id"]
        except SalesforceError as e:
            print("_______ error get_id_profile _______", str(e))
            raise_exception_salesforce(e)

    def get_id_permission_set(self, profile_id: str):
        self.refresh_client()
        try:
            query = f"""
                SELECT Id FROM PermissionSet WHERE ProfileId='{profile_id}'
            """
            resp = self.client.query(query)
            if not resp.get("records") or len(resp["records"]) == 0:
                return None
            return resp["records"][0]["Id"]
        except SalesforceError as e:
            print("_______ error get_id_permission_set _______", str(e))
            raise_exception_salesforce(e)

    def update_field_level_security(
        self, field_name: str, permission_set_ids: List[str]
    ):
        self.refresh_client()
        responses = []
        # Metadata API endpoint for FieldPermissions
        metadata_url = (
            f"{self.instance_url}/services/data/v63.0/sobjects/FieldPermissions/"
        )
        for permission_set_id in permission_set_ids:
            try:
                # Construct the FieldPermissions metadata
                field_permissions = {
                    "ParentId": permission_set_id,  # Profile ID
                    "Field": field_name,  # API name of the field
                    "PermissionsRead": True,  # Whether the field is readable
                    "PermissionsEdit": True,  # Whether the field is editable
                    "SobjectType": "Account",
                }

                # Set the headers, including the Authorization (Bearer token)
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                }

                # Send POST request to update Field-Level Security
                response = requests.post(
                    metadata_url, headers=headers, json=field_permissions
                )

                if response.status_code != 201 and response.status_code != 200:
                    print(
                        f"Failed to update field level security: {response.status_code}"
                    )
                    error = ""
                    if hasattr(response, "content"):
                        error = str(response.content)
                    elif hasattr(response, "text"):
                        error = str(response.text)
                    else:
                        error = str(response)
                    raise HTTPException(status_code=400, detail=error)
                else:
                    responses.append(response)
            except HTTPException as e:
                print("_______ error update_field_level_security _______", str(e))
                raise_exception_salesforce(e)
        return responses

    def check_api_enabled(self):
        self.refresh_client()
        url = f"{self.instance_url}/services/data/v63.0/"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.get(url, headers=headers)

            if response.status_code != 200 and response.status_code != 201:
                print("_______ error check_api_enabled _______", response.json())
                raise HTTPException(
                    status_code=response.status_code, detail=response.json()
                )
            else:
                print(response.json())
                return True
        except HTTPException as e:
            print("_______ error check_api_enabled _______", str(e.detail))
            raise_exception_salesforce(e)


def get_token_salesforce(code: str):
    try:
        auth_data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.SALESFORCE_CLIENT_ID,
            "client_secret": settings.SALESFORCE_CLIENT_SECRET,
            "redirect_uri": settings.SALESFORCE_REDIRECT_URI,
        }
        response = requests.post(settings.SALESFORCE_TOKEN_URL, data=auth_data)

        if response.status_code != 200 and response.status_code != 201:
            print("_______ error get_token_salesforce _______", response.json())
            raise HTTPException(
                status_code=response.status_code, detail=response.json()
            )

        response_data = response.json()

        return (
            response_data["access_token"],
            response_data["refresh_token"],
            response_data["instance_url"],
            response_data["id"],
        )
    except HTTPException as e:
        print("_______ error get_token_salesforce _______", str(e))
        raise_exception_salesforce(e)


def raise_exception_salesforce(e: Union[HTTPException, Exception, SalesforceError]):
    error = ""
    if hasattr(e, "content"):
        error = str(e.content)
    elif hasattr(e, "body"):
        error = str(e.body)
    elif hasattr(e, "detail"):
        error = str(e.detail)
    elif hasattr(e, "response") and hasattr(e.response, "text"):
        error = str(e.response.text)
    else:
        error = str(e)
    print("_______ str error raise_exception_salesforce  _______", error)
    # errorCode in salesforce error response
    if "APEX_REST_SERVICES_DISABLED" in error:
        raise ConflictException(detail=error)
    if "API_CURRENTLY_DISABLED" in error:
        raise ConflictException(detail=error)
    if "API_DISABLED_FOR_ORG" in error:
        raise ConflictException(detail=error)
    if "BIG_OBJECT_UNSUPPORTED_OPERATION" in error:
        raise ConflictException(detail=error)
    if "BILLING_ENTITIES_NO_ACCESS" in error:
        raise ConflictException(detail=error)
    if "CANNOT_UPDATE_IS_THIRD_PARTY" in error:
        raise ConflictException(detail=error)
    if "CANT_ADD_STANDARD_PORTAL_USER_TO_TERRITORY" in error:
        raise ConflictException(detail=error)
    if "CART_NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "CATEGORY_NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "CHECKOUT_CONFLICT" in error:
        raise ConflictException(detail=error)
    if "CHECKOUT_EXPIRED" in error:
        raise ConflictException(detail=error)
    if "CHECKOUT_INVALIDATED" in error:
        raise ConflictException(detail=error)
    if "CHECKOUT_LOCKED" in error:
        raise ConflictException(detail=error)
    if "CHECKOUT_NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "CIRCULAR_OBJECT_GRAPH" in error:
        raise ConflictException(detail=error)
    if "CLIENT_NOT_ACCESSIBLE_FOR_USER" in error:
        raise ConflictException(detail=error)
    if "CLIENT_REQUIRE_UPDATE_FOR_USER" in error:
        raise ConflictException(detail=error)
    if "CLONE_NOT_SUPPORTED" in error:
        raise ConflictException(detail=error)
    if "CLONE_FIELD_INTEGRITY_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "COMMERCE_ADMIN_MISCONFIGURATION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_ALREADY_AN_ASSET_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_HUB_AUTHENTICATION_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_HUB_FILE_HAS_NO_URL_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_HUB_FILE_NOT_FOUND_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_HUB_INVALID_PAGE_NUMBER_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_CUSTOM_DOWNLOAD_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_HUB_INVALID_OBJECT_TYPE_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_HUB_INVALID_RENDITION_PAGE_NUMBER_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_HUB_ITEM_TYPE_NOT_FOUND_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_HUB_OBJECT_NOT_FOUND_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_HUB_OPERATION_NOT_SUPPORTED_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_HUB_SECURITY_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_HUB_TIMEOUT_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_HUB_UNEXPECTED_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_IMAGE_SCALING_INVALID_ARGUMENTS_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_IMAGE_SCALING_INVALID_IMAGE_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_IMAGE_SCALING_MAX_RENDITIONS_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_IMAGE_SCALING_TIMEOUT_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "CONTENT_IMAGE_SCALING_UNKNOWN_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "DELETE_REQUIRED_ON_CASCADE" in error:
        raise ConflictException(detail=error)
    if "DEPENDENCY_API_UNSUPPORTED_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "DUPLICATE_COMM_NICKNAME" in error:
        raise ConflictException(detail=error)
    if "DUPLICATE_VALUE" in error:
        raise ConflictException(detail=error)
    if "EMAIL_BATCH_SIZE_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "EMAIL_TO_CASE_INVALID_ROUTING" in error:
        raise ConflictException(detail=error)
    if "EMAIL_TO_CASE_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "EMAIL_TO_CASE_NOT_ENABLED" in error:
        raise ConflictException(detail=error)
    if "ENTITY_NOT_QUERYABLE" in error:
        raise ConflictException(detail=error)
    if "EXCEEDED_ID_LIMIT" in error:
        raise ConflictException(detail=error)
    if "EXCEEDED_LEAD_CONVERT_LIMIT" in error:
        raise ConflictException(detail=error)
    if "EXCEEDED_MAX_SEMIJOIN_SUBSELECTS" in error:
        raise ConflictException(detail=error)
    if "EXCEEDED_MAX_SIZE_REQUEST" in error:
        raise ConflictException(detail=error)
    if "EXCEEDED_MAX_TYPES_LIMIT" in error:
        raise ConflictException(detail=error)
    if "EXCEEDED_QUOTA" in error:
        raise ConflictException(detail=error)
    if "EXTERNAL_SERVICE_CONNECTION_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "EXTERNAL_SERVICE_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "EXTERNAL_SERVICE_INVALID_STATE_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "GONE" in error:
        raise ConflictException(detail=error)
    if "IAS_TIMEOUT_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "IAS_NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "ID_REQUIRED" in error:
        raise ConflictException(detail=error)
    if "IDEMPOTENCY_FEATURE_NOT_ENABLED" in error:
        raise ConflictException(detail=error)
    if "IDEMPOTENCY_NOT_SUPPORTED" in error:
        raise ConflictException(detail=error)
    if "INACTIVE_OWNER_OR_USER" in error:
        raise ConflictException(detail=error)
    if "INACTIVE_PORTAL" in error:
        raise ConflictException(detail=error)
    if "INDEX_NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "INSTALL_KEY_INVALID" in error:
        raise ConflictException(detail=error)
    if "INSTALL_KEY_REQUIRED" in error:
        raise ConflictException(detail=error)
    if "INSUFFICIENT_ACCESS_APEX_METADATA_DEPLOY" in error:
        raise ConflictException(detail=error)
    if "INSUFFICIENT_BENEFIT_REMAINING" in error:
        raise ConflictException(detail=error)
    if "INTERNAL_ERROR" in error:
        raise ConflictException(detail=error)
    if "INVALID_ACCOUNTING_SET" in error:
        raise ConflictException(detail=error)
    if "INVALID_ASSIGNMENT_RULE" in error:
        raise ConflictException(detail=error)
    if "INVALID_BATCH_REQUEST" in error:
        raise ConflictException(detail=error)
    if "INVALID_BATCH_SIZE" in error:
        raise ConflictException(detail=error)
    if "INVALID_CLIENT" in error:
        raise ConflictException(detail=error)
    if "INVALID_CROSS_REFERENCE_KEY" in error:
        raise ConflictException(detail=error)
    if "INVALID_DEFINITION" in error:
        raise ConflictException(detail=error)
    if "INVALID_FILTER_LANGUAGE" in error:
        raise ConflictException(detail=error)
    if "INVALID_FILTER_VALUE" in error:
        raise ConflictException(detail=error)
    if "INVALID_GOOGLE_DOCS_URL" in error:
        raise ConflictException(detail=error)
    if "INVALID_ID_FIELD" in error:
        raise ConflictException(detail=error)
    if "INVALID_IDEMPOTENCY_KEY" in error:
        raise ConflictException(detail=error)
    if "INVALID_INPUT" in error:
        raise ConflictException(detail=error)
    if "INVALID_LOCATOR" in error:
        raise ConflictException(detail=error)
    if "INVALID_LOGIN" in error:
        raise ConflictException(detail=error)
    if "INVALID_NEW_PASSWORD" in error:
        raise ConflictException(detail=error)
    if "INVALID_OPERATION_WITH_EXPIRED_PASSWORD" in error:
        raise ConflictException(detail=error)
    if "INVALID_OPERATION" in error:
        raise ConflictException(detail=error)
    if "INVALID_QUERY_FILTER_OPERATOR" in error:
        raise ConflictException(detail=error)
    if "INVALID_QUERY_KEY" in error:
        raise ConflictException(detail=error)
    if "INVALID_QUERY_SCOPE" in error:
        raise ConflictException(detail=error)
    if "INVALID_QUERY_VALUE" in error:
        raise ConflictException(detail=error)
    if "INVALID_REPLICATION_DATE" in error:
        raise ConflictException(detail=error)
    if "INVALID_RECORD_ATTRIBUTE_VALUE" in error:
        raise ConflictException(detail=error)
    if "INVALID_RUNTIME_VALUE" in error:
        raise ConflictException(detail=error)
    if "INVALID_SETUP_OWNER" in error:
        raise ConflictException(detail=error)
    if "INVALID_SEARCH_SCOPE" in error:
        raise ConflictException(detail=error)
    if "INVALID_SEARCH" in error:
        raise ConflictException(detail=error)
    if "INVALID_SOAP_HEADER" in error:
        raise ConflictException(detail=error)
    if "INVALID_SSO_GATEWAY_URL" in error:
        raise ConflictException(detail=error)
    if "INVALID_VERSION" in error:
        raise ConflictException(detail=error)
    if "KEY_HAS_BEEN_DESTROYED" in error:
        raise ConflictException(detail=error)
    if "LOGIN_CHALLENGE_ISSUED" in error:
        raise ConflictException(detail=error)
    if "LOGIN_CHALLENGE_PENDING" in error:
        raise ConflictException(detail=error)
    if "LOGIN_DURING_RESTRICTED_DOMAIN" in error:
        raise ConflictException(detail=error)
    if "LOGIN_DURING_RESTRICTED_TIME" in error:
        raise ConflictException(detail=error)
    if "LOGIN_MUST_USE_SECURITY_TOKEN" in error:
        raise ConflictException(detail=error)
    if "MALFORMED_ID" in error:
        raise ConflictException(detail=error)
    if "MALFORMED_QUERY" in error:
        raise ConflictException(detail=error)
    if "MALFORMED_SEARCH" in error:
        raise ConflictException(detail=error)
    if "MISMATCHING_VERSIONS" in error:
        raise ConflictException(detail=error)
    if "MISSING_ARGUMENT" in error:
        raise ConflictException(detail=error)
    if "MIXED_DML_OPERATION" in error:
        raise ConflictException(detail=error)
    if "MULTIPLE_RECORDS_FOUND" in error:
        raise ConflictException(detail=error)
    if "NO_DEFINITION_ASSOCIATED" in error:
        raise ConflictException(detail=error)
    if "NOT_ACCEPTABLE" in error:
        raise ConflictException(detail=error)
    if "NOT_MODIFIED" in error:
        raise ConflictException(detail=error)
    if "NO_SOFTPHONE_LAYOUT" in error:
        raise ConflictException(detail=error)
    if "NO_RECIPIENTS" in error:
        raise ConflictException(detail=error)
    if "NUMBER_OUTSIDE_VALID_RANGE" in error:
        raise ConflictException(detail=error)
    if "OPERATION_TOO_LARGE" in error:
        raise ConflictException(detail=error)
    if "ORDER_MANAGEMENT_ACTION_NOT_ALLOWED" in error:
        raise ConflictException(detail=error)
    if "ORG_LOCKED" in error:
        raise ConflictException(detail=error)
    if "ORG_NOT_OWNED_BY_INSTANCE" in error:
        raise ConflictException(detail=error)
    if "PARAMETER_TOO_LARGE" in error:
        raise ConflictException(detail=error)
    if "PASSWORD_LOCKOUT" in error:
        raise ConflictException(detail=error)
    if "PAYLOAD_ITEM_MAP_ERROR" in error:
        raise ConflictException(detail=error)
    if "PORTAL_NO_ACCESS" in error:
        raise ConflictException(detail=error)
    if "PRODUCT_NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "QUERY_TIMEOUT" in error:
        raise ConflictException(detail=error)
    if "QUERY_TOO_COMPLICATED" in error:
        raise ConflictException(detail=error)
    if "REALTIME_PROCESSING_TIME_EXCEEDED_LIMIT" in error:
        raise ConflictException(detail=error)
    if "REPORT_EXPORT_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "REQUEST_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "REQUEST_RUNNING_TOO_LONG" in error:
        raise ConflictException(detail=error)
    if "SERVER_UNAVAILABLE" in error:
        raise ConflictException(detail=error)
    if "SPECIFICATION_GENERAL_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "SSO_SERVICE_DOWN" in error:
        raise ConflictException(detail=error)
    if "STATE_TRANSITION_NOT_ALLOWED" in error:
        raise ConflictException(detail=error)
    if "TOO_MANY_APEX_REQUESTS" in error:
        raise ConflictException(detail=error)
    if "TRIAL_EXPIRED" in error:
        raise ConflictException(detail=error)
    if "TXN_SECURITY_APEX_ERROR" in error:
        raise ConflictException(detail=error)
    if "TXN_SECURITY_METERING_ERROR" in error:
        raise ConflictException(detail=error)
    if "TXN_SECURITY_RUNTIME_ERROR" in error:
        raise ConflictException(detail=error)
    if "UNSUPPORTED_API_VERSION" in error:
        raise ConflictException(detail=error)
    if "UNSUPPORTED_CLIENT" in error:
        raise ConflictException(detail=error)
    if "WEBSTORE_NOT_FOUND" in error:
        raise ConflictException(detail=error)

    # statusCode in salesforce error response
    if "APEX_DATA_ACCESS_RESTRICTION" in error:
        raise ConflictException(detail=error)
    if "ALL_OR_NONE_OPERATION_ROLLED_BACK" in error:
        raise ConflictException(detail=error)
    if "ALREADY_APPLIED" in error:
        raise ConflictException(detail=error)
    if "ALREADY_IN_PROCESS" in error:
        raise ConflictException(detail=error)
    if "ASSIGNEE_TYPE_REQUIRED" in error:
        raise ConflictException(detail=error)
    if "AURA_COMPILE_ERROR" in error:
        raise ConflictException(detail=error)
    if "AUTH_PROVIDER_NEEDS_AUTH" in error:
        raise ConflictException(detail=error)
    if "AUTH_PROVIDER_NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "BAD_CUSTOM_ENTITY_PARENT_DOMAIN" in error:
        raise ConflictException(detail=error)
    if "BAD_REQUEST" in error:
        raise ConflictException(detail=error)
    if "BCC_NOT_ALLOWED_IF_BCC_COMPLIANCE_ENABLED" in error:
        raise ConflictException(detail=error)
    if "BCC_SELF_NOT_ALLOWED_IF_BCC_COMPLIANCE_ENABLED" in error:
        raise ConflictException(detail=error)
    if "CANNOT_CASCADE_PRODUCT_ACTIVE" in error:
        raise ConflictException(detail=error)
    if "CANNOT_CHANGE_FIELD_TYPE_OF_APEX_REFERENCED_FIELD" in error:
        raise ConflictException(detail=error)
    if "CANNOT_CREATE_ANOTHER_MANAGED_PACKAGE" in error:
        raise ConflictException(detail=error)
    if "CANNOT_DEACTIVATE_DIVISION" in error:
        raise ConflictException(detail=error)
    if "CANNOT_DELETE_LAST_DATED_CONVERSION_RATE" in error:
        raise ConflictException(detail=error)
    if "CANNOT_DELETE_MANAGED_OBJECT" in error:
        raise ConflictException(detail=error)
    if "CANNOT_DISABLE_LAST_ADMIN" in error:
        raise ConflictException(detail=error)
    if "CANNOT_ENABLE_IP_RESTRICT_REQUESTS" in error:
        raise ConflictException(detail=error)
    if "CANNOT_EXECUTE_FLOW_TRIGGER" in error:
        raise ConflictException(detail=error)
    if "CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY" in error:
        raise ConflictException(detail=error)
    if "CANNOT_MODIFY_MANAGED_OBJECT" in error:
        raise ConflictException(detail=error)
    if "CANNOT_RENAME_APEX_REFERENCED_FIELD" in error:
        raise ConflictException(detail=error)
    if "CANNOT_RENAME_APEX_REFERENCED_OBJECT" in error:
        raise ConflictException(detail=error)
    if "CANNOT_REPARENT_RECORD" in error:
        raise ConflictException(detail=error)
    if "CANNOT_RESOLVE_NAME" in error:
        raise ConflictException(detail=error)
    if "CANNOT_UPDATE_CONVERTED_LEAD" in error:
        raise ConflictException(detail=error)
    if "CANNOT_POST_TO_ARCHIVED_GROUP" in error:
        raise ConflictException(detail=error)
    if "CANT_DISABLE_CORP_CURRENCY" in error:
        raise ConflictException(detail=error)
    if "CANT_UNSET_CORP_CURRENCY" in error:
        raise ConflictException(detail=error)
    if "CHECKOUT_UNAUTHORIZED" in error:
        raise ConflictException(detail=error)
    if "CHILD_SHARE_FAILS_PARENT" in error:
        raise ConflictException(detail=error)
    if "CIRCULAR_DEPENDENCY" in error:
        raise ConflictException(detail=error)
    if "COMMUNITY_NOT_ACCESSIBLE" in error:
        raise ConflictException(detail=error)
    if "CONFLICTING_ENVIRONMENT_HUB_MEMBER" in error:
        raise ConflictException(detail=error)
    if "CONFLICTING_SSO_USER_MAPPING" in error:
        raise ConflictException(detail=error)
    if "CONTENT_NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "CONTENT_TYPE_NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "COUPON_REDEMPTION_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "CUSTOM_CLOB_FIELD_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "CUSTOM_ENTITY_OR_FIELD_LIMIT" in error:
        raise ConflictException(detail=error)
    if "CUSTOM_FIELD_INDEX_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "CUSTOM_INDEX_EXISTS" in error:
        raise ConflictException(detail=error)
    if "CUSTOM_LINK_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "CUSTOM_METADATA_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "CUSTOM_SETTINGS_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "CUSTOM_TAB_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "DATACLOUDADDRESS_NO_RECORDS_FOUND" in error:
        raise ConflictException(detail=error)
    if "DATACLOUDADDRESS_PROCESSING_ERROR" in error:
        raise ConflictException(detail=error)
    if "DATACLOUDADDRESS_SERVER_ERROR" in error:
        raise ConflictException(detail=error)
    if "DEPENDENCY_EXISTS" in error:
        raise ConflictException(detail=error)
    if "DUPLICATE_CASE_SOLUTION" in error:
        raise ConflictException(detail=error)
    if "DUPLICATE_CUSTOM_ENTITY_DEFINITION" in error:
        raise ConflictException(detail=error)
    if "DUPLICATE_CUSTOM_TAB_MOTIF" in error:
        raise ConflictException(detail=error)
    if "DUPLICATE_DEVELOPER_NAME" in error:
        raise ConflictException(detail=error)
    if "DUPLICATES_DETECTED" in error:
        raise ConflictException(detail=error)
    if "DUPLICATE_EXTERNAL_ID" in error:
        raise ConflictException(detail=error)
    if "DUPLICATE_MASTER_LABEL" in error:
        raise ConflictException(detail=error)
    if "DUPLICATE_SENDER_DISPLAY_NAME" in error:
        raise ConflictException(detail=error)
    if "DUPLICATE_USERNAME" in error:
        raise ConflictException(detail=error)
    if "EMAIL_ADDRESS_BOUNCED" in error:
        raise ConflictException(detail=error)
    if "EMAIL_EXTERNAL_TRANSPORT_PERMISSION_ERROR" in error:
        raise ConflictException(detail=error)
    if "EMAIL_EXTERNAL_TRANSPORT_TOO_MANY_REQUESTS_ERROR" in error:
        raise ConflictException(detail=error)
    if "EMAIL_NOT_PROCESSED_DUE_TO_PRIOR_ERROR" in error:
        raise ConflictException(detail=error)
    if "EMAIL_OPTED_OUT" in error:
        raise ConflictException(detail=error)
    if "EMAIL_TEMPLATE_FORMULA_ERROR" in error:
        raise ConflictException(detail=error)
    if "EMAIL_TEMPLATE_MERGEFIELD_ACCESS_ERROR" in error:
        raise ConflictException(detail=error)
    if "EMAIL_TEMPLATE_MERGEFIELD_ERROR" in error:
        raise ConflictException(detail=error)
    if "EMAIL_TEMPLATE_MERGEFIELD_VALUE_ERROR" in error:
        raise ConflictException(detail=error)
    if "EMAIL_TEMPLATE_PROCESSING_ERROR" in error:
        raise ConflictException(detail=error)
    if "EMPTY_SCONTROL_FILE_NAME" in error:
        raise ConflictException(detail=error)
    if "ENTITY_FAILED_IFLASTMODIFIED_ON_UPDATE" in error:
        raise ConflictException(detail=error)
    if "MODIFIED" in error:
        raise ConflictException(detail=error)
    if "ENTITY_IS_ARCHIVED" in error:
        raise ConflictException(detail=error)
    if "ENTITY_IS_DELETED" in error:
        raise ConflictException(detail=error)
    if "ENTITY_IS_LOCKED" in error:
        raise ConflictException(detail=error)
    if "ENVIRONMENT_HUB_MEMBERSHIP_CONFLICT" in error:
        raise ConflictException(detail=error)
    if "CONFLICT" in error:
        raise ConflictException(detail=error)
    if "ERROR_IN_MAILER" in error:
        raise ConflictException(detail=error)
    if "EXCEEDED_MAX_SEMIJOIN_SUBSELECTS_WRITE" in error:
        raise ConflictException(detail=error)
    if "EXCHANGE_WEB_SERVICES_URL_INVALID" in error:
        raise ConflictException(detail=error)
    if "EXTERNAL_RESOURCE_FORBIDDEN" in error:
        raise ConflictException(detail=error)
    if "FAILED_ACTIVATION" in error:
        raise ConflictException(detail=error)
    if "FIELD_CUSTOM_VALIDATION_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "FIELD_FILTER_VALIDATION_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "FIELD_KEYWORD_LIST_MATCH_LIMIT" in error:
        raise ConflictException(detail=error)
    if "FILE_EXTENSION_NOT_ALLOWED" in error:
        raise ConflictException(detail=error)
    if "FILE_SIZE_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "FILTERED_LOOKUP_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "FIELD_MAPPING_ERROR" in error:
        raise ConflictException(detail=error)
    if "FIELD_MODERATION_RULE_BLOCK" in error:
        raise ConflictException(detail=error)
    if "FLOW_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "FUNCTIONALITY_NOT_ENABLED" in error:
        raise ConflictException(detail=error)
    if "HAS_PUBLIC_REFERENCES" in error:
        raise ConflictException(detail=error)
    if "HTML_FILE_UPLOAD_NOT_ALLOWED" in error:
        raise ConflictException(detail=error)
    if "IMAGE_TOO_LARGE" in error:
        raise ConflictException(detail=error)
    if "IAS_UNCOMITTED_WORK" in error:
        raise ConflictException(detail=error)
    if "INPUTPARAM_INCOMPATIBLE_DATATYPE" in error:
        raise ConflictException(detail=error)
    if "INSERT_UPDATE_DELETE_NOT_ALLOWED_DURING_MAINTENANCE" in error:
        raise ConflictException(detail=error)
    if "INSUFFICIENT_ACCESS_ON_CROSS_REFERENCE_ENTITY" in error:
        raise ConflictException(detail=error)
    if "INSUFFICIENT_ACCESS_OR_READONLY" in error:
        raise ConflictException(detail=error)
    if "INSUFFICIENT_ACCESS_TO_INSIGHTSEXTERNALDATA" in error:
        raise ConflictException(detail=error)
    if "INSUFFICIENT_ACCESS" in error:
        raise ConflictException(detail=error)
    if "INSUFFICIENT_BALANCE" in error:
        raise ConflictException(detail=error)
    if "INVALID_ACCESS_LEVEL" in error:
        raise ConflictException(detail=error)
    if "INVALID_ACCESS_TOKEN" in error:
        raise ConflictException(detail=error)
    if "INVALID_ACCOUNT" in error:
        raise ConflictException(detail=error)
    if "INVALID_ARGUMENT_TYPE" in error:
        raise ConflictException(detail=error)
    if "INVALID_ASSIGNEE_TYPE" in error:
        raise ConflictException(detail=error)
    if "INVALID_AUTH_HEADER" in error:
        raise ConflictException(detail=error)
    if "INVALID_BATCH_OPERATION" in error:
        raise ConflictException(detail=error)
    if "INVALID_CHECKOUT_INPUT" in error:
        raise ConflictException(detail=error)
    if "INVALID_CONTENT_TYPE" in error:
        raise ConflictException(detail=error)
    if "INVALID_COUPON" in error:
        raise ConflictException(detail=error)
    if "INVALID_CREDIT_CARD_INFO" in error:
        raise ConflictException(detail=error)
    if "INVALID_CROSS_REFERENCE_TYPE_FOR_FIELD" in error:
        raise ConflictException(detail=error)
    if "INVALID_CONTACT" in error:
        raise ConflictException(detail=error)
    if "INVALID_CURRENCY_CONV_RATE" in error:
        raise ConflictException(detail=error)
    if "INVALID_CURRENCY_CORP_RATE" in error:
        raise ConflictException(detail=error)
    if "INVALID_CURRENCY_ISO" in error:
        raise ConflictException(detail=error)
    if "INVALID_EMAIL_ADDRESS" in error:
        raise ConflictException(detail=error)
    if "INVALID_EMPTY_KEY_OWNER" in error:
        raise ConflictException(detail=error)
    if "INVALID_ENTITY_FOR_UPSERT" in error:
        raise ConflictException(detail=error)
    if "INVALID_ENVIRONMENT_HUB_MEMBER" in error:
        raise ConflictException(detail=error)
    if "INVALID_EVENT_DELIVERY" in error:
        raise ConflictException(detail=error)
    if "INVALID_EVENT_SUBSCRIPTION" in error:
        raise ConflictException(detail=error)
    if "INVALID_EXTERNAL_ID_FIELD_NAME" in error:
        raise ConflictException(detail=error)
    if "INVALID_FIELD_FOR_INSERT_UPDATE" in error:
        raise ConflictException(detail=error)
    if "INVALID_FIELD_WHEN_USING_TEMPLATE" in error:
        raise ConflictException(detail=error)
    if "INVALID_FIELD" in error:
        raise ConflictException(detail=error)
    if "INVALID_FILTER_ACTION" in error:
        raise ConflictException(detail=error)
    if "INVALID_INET_ADDRESS" in error:
        raise ConflictException(detail=error)
    if "INVALID_LINEITEM_CLONE_STATE" in error:
        raise ConflictException(detail=error)
    if "INVALID_MARKUP" in error:
        raise ConflictException(detail=error)
    if "INVALID_MERCHANT_ACCOUNT_MODE_OR_STATUS" in error:
        raise ConflictException(detail=error)
    if "INVALID_MERCHANT_ACCOUNT_MODE" in error:
        raise ConflictException(detail=error)
    if "INVALID_MERGE_RECORD" in error:
        raise ConflictException(detail=error)
    if "INVALID_MASTER_OR_TRANSLATED_SOLUTION" in error:
        raise ConflictException(detail=error)
    if "INVALID_MESSAGE_ID_REFERENCE" in error:
        raise ConflictException(detail=error)
    if "INVALID_NAMESPACE_PREFIX" in error:
        raise ConflictException(detail=error)
    if "INVALID_OPERATOR" in error:
        raise ConflictException(detail=error)
    if "INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST" in error:
        raise ConflictException(detail=error)
    if "INVALID_PACKAGE_LICENSE" in error:
        raise ConflictException(detail=error)
    if "INVALID_PARTNER_NETWORK_STATUS" in error:
        raise ConflictException(detail=error)
    if "INVALID_PERSON_ACCOUNT_OPERATION" in error:
        raise ConflictException(detail=error)
    if "INVALID_PROFILE" in error:
        raise ConflictException(detail=error)
    if "INVALID_READ_ONLY_USER_DML" in error:
        raise ConflictException(detail=error)
    if "INVALID_RECEIVEDDOCUMENTID_ATTACHMENT" in error:
        raise ConflictException(detail=error)
    if "INVALID_RECORD_TYPE" in error:
        raise ConflictException(detail=error)
    if "INVALID_REFRESH_TOKEN" in error:
        raise ConflictException(detail=error)
    if "INVALID_SAVE_AS_ACTIVITY_FLAG" in error:
        raise ConflictException(detail=error)
    if "INVALID_SCS_INBOUND_USER" in error:
        raise ConflictException(detail=error)
    if "INVALID_SESSION_ID" in error:
        raise ConflictException(detail=error)
    if "INVALID_SERVER_ERROR" in error:
        raise ConflictException(detail=error)
    if "INVALID_SIGNUP_OPTION" in error:
        raise ConflictException(detail=error)
    if "INVALID_STATUS" in error:
        raise ConflictException(detail=error)
    if "INVALID_TARGET_OBJECT_NAME" in error:
        raise ConflictException(detail=error)
    if "INVALID_TYPE_FOR_OPERATION" in error:
        raise ConflictException(detail=error)
    if "INVALID_TYPE_ON_FIELD_IN_RECORD" in error:
        raise ConflictException(detail=error)
    if "INVALID_TYPE" in error:
        raise ConflictException(detail=error)
    if "INVALID_UNMERGE_RECORD" in error:
        raise ConflictException(detail=error)
    if "INVALID_USERID" in error:
        raise ConflictException(detail=error)
    if "INVALID_USER_OBJECT" in error:
        raise ConflictException(detail=error)
    if "IP_RANGE_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "JIGSAW_IMPORT_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "LICENSE_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "LIGHT_PORTAL_USER_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "MANAGER_NOT_DEFINED" in error:
        raise ConflictException(detail=error)
    if "MASSMAIL_RETRY_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "MASS_MAIL_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "MATCH_PRECONDITION_REQUIRED" in error:
        raise ConflictException(detail=error)
    if "MATCH_PRECONDITION_FAILED" in error:
        raise ConflictException(detail=error)
    if "MAXIMUM_CCEMAILS_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "MAXIMUM_DASHBOARD_COMPONENTS_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "MAXIMUM_HIERARCHY_CHILDREN_REACHED" in error:
        raise ConflictException(detail=error)
    if "MAXIMUM_HIERARCHY_LEVELS_REACHED" in error:
        raise ConflictException(detail=error)
    if "MAXIMUM_SIZE_OF_ATTACHMENT" in error:
        raise ConflictException(detail=error)
    if "MAXIMUM_SIZE_OF_DOCUMENT" in error:
        raise ConflictException(detail=error)
    if "MAX_ACTIONS_PER_RULE_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "MAX_ACTIVE_RULES_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "MAX_APPROVAL_STEPS_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "MAX_DEPTH_IN_FLOW_EXECUTION" in error:
        raise ConflictException(detail=error)
    if "MAX_FORMULAS_PER_RULE_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "MAX_RULES_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "MAX_RULE_ENTRIES_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "MAX_TASK_DESCRIPTION_EXCEEEDED" in error:
        raise ConflictException(detail=error)
    if "MAX_TM_RULES_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "MAX_TM_RULE_ITEMS_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "MAX_TRIGGERS_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "MERGE_FAILED" in error:
        raise ConflictException(detail=error)
    if "METHOD_NOT_ALLOWED" in error:
        raise ConflictException(detail=error)
    if "METADATA_FIELD_UPDATE_ERROR" in error:
        raise ConflictException(detail=error)
    if "MISMATCHING_TYPES" in error:
        raise ConflictException(detail=error)
    if "MISSING_OMNI_PROCESS_ID" in error:
        raise ConflictException(detail=error)
    if "NONUNIQUE_SHIPPING_ADDRESS" in error:
        raise ConflictException(detail=error)
    if "NO_APPLICABLE_PROCESS" in error:
        raise ConflictException(detail=error)
    if "NO_ATTACHMENT_PERMISSION" in error:
        raise ConflictException(detail=error)
    if "NO_INACTIVE_DIVISION_MEMBERS" in error:
        raise ConflictException(detail=error)
    if "NO_MASS_MAIL_PERMISSION" in error:
        raise ConflictException(detail=error)
    if "NO_PARTNER_PERMISSION" in error:
        raise ConflictException(detail=error)
    if "NUM_HISTORY_FIELDS_BY_SOBJECT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "OP_WITH_INVALID_USER_TYPE_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "OPERATION_ENQUEUED" in error:
        raise ConflictException(detail=error)
    if "OPTED_OUT_OF_MASS_MAIL" in error:
        raise ConflictException(detail=error)
    if "ORDER_MANAGEMENT_INVALID_RECORD" in error:
        raise ConflictException(detail=error)
    if "ORDER_MANAGEMENT_RECORD_EXISTS" in error:
        raise ConflictException(detail=error)
    if "ORDER_MANAGEMENT_RECORD_NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "RECORD_NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "PA_API_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "PA_AXIS_FAULT" in error:
        raise ConflictException(detail=error)
    if "PA_INVALID_ID_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "PA_NO_ACCESS_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "PA_NO_DATA_FOUND_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "PA_URI_SYNTAX_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "PA_VISIBLE_ACTIONS_FILTER_ORDERING_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "PACKAGE_DISABLED" in error:
        raise ConflictException(detail=error)
    if "PACKAGE_LICENSE_REQUIRED" in error:
        raise ConflictException(detail=error)
    if "PAL_INVALID_ASSISTANT_RECOMMENDATION_TYPE_ID" in error:
        raise ConflictException(detail=error)
    if "PAL_INVALID_ENTITY_ID" in error:
        raise ConflictException(detail=error)
    if "PAL_INVALID_FLEXIPAGE_ID" in error:
        raise ConflictException(detail=error)
    if "PAL_INVALID_LAYOUT_ID" in error:
        raise ConflictException(detail=error)
    if "PAL_INVALID_PARAMETERS" in error:
        raise ConflictException(detail=error)
    if "PALI_INVALID_ACTION_ID" in error:
        raise ConflictException(detail=error)
    if "PALI_INVALID_ACTION_NAME" in error:
        raise ConflictException(detail=error)
    if "PALI_INVALID_ACTION_TYPE" in error:
        raise ConflictException(detail=error)
    if "PARTICIPANT_RELATIONSHIP_EXISTS" in error:
        raise ConflictException(detail=error)
    if "PLATFORM_EVENT_ENCRYPTION_ERROR" in error:
        raise ConflictException(detail=error)
    if "PLATFORM_EVENT_PUBLISHING_UNAVAILABLE" in error:
        raise ConflictException(detail=error)
    if "PLATFORM_EVENT_PUBLISH_FAILED" in error:
        raise ConflictException(detail=error)
    if "PORTAL_USER_ALREADY_EXISTS_FOR_CONTACT" in error:
        raise ConflictException(detail=error)
    if "PORTAL_USER_CREATION_RESTRICTED_WITH_ENCRYPTION" in error:
        raise ConflictException(detail=error)
    if "PRIVATE_CONTACT_ON_ASSET" in error:
        raise ConflictException(detail=error)
    if "PROCESSING_HALTED" in error:
        raise ConflictException(detail=error)
    if "QA_INVALID_CREATE_FEED_ITEM" in error:
        raise ConflictException(detail=error)
    if "QA_INVALID_SUCCESS_MESSAGE" in error:
        raise ConflictException(detail=error)
    if "QUICK_ACTION_LIST_ITEM_NOT_ALLOWED" in error:
        raise ConflictException(detail=error)
    if "QUICK_ACTION_LIST_NOT_ALLOWED" in error:
        raise ConflictException(detail=error)
    if "RECORD_IN_USE_BY_WORKFLOW" in error:
        raise ConflictException(detail=error)
    if "RELATED_ENTITY_FILTER_VALIDATION_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "REL_FIELD_BAD_ACCESSIBILITY" in error:
        raise ConflictException(detail=error)
    if "REPUTATION_MINIMUM_NUMBER_NOT_REACHED" in error:
        raise ConflictException(detail=error)
    if "REQUIRE_CONNECTED_APP_SCS" in error:
        raise ConflictException(detail=error)
    if "REQUIRE_CONNECTED_APP_SESSION_SCS" in error:
        raise ConflictException(detail=error)
    if "REQUIRE_RUNAS_USER" in error:
        raise ConflictException(detail=error)
    if "REQUIRED_FIELD_MISSING" in error:
        raise ConflictException(detail=error)
    if "RETRIEVE_EXCHANGE_ATTACHMENT_FAILED" in error:
        raise ConflictException(detail=error)
    if "RETRIEVE_EXCHANGE_EMAIL_FAILED" in error:
        raise ConflictException(detail=error)
    if "RETRIEVE_EXCHANGE_EVENT_FAILED" in error:
        raise ConflictException(detail=error)
    if "RETRIEVE_USER_CONFIG_ERROR" in error:
        raise ConflictException(detail=error)
    if "ROUTES_EVALUATION_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "SALESFORCE_INBOX_TRANSPORT_CONNECTION_ERROR" in error:
        raise ConflictException(detail=error)
    if "SALESFORCE_INBOX_TRANSPORT_TOKEN_ERROR" in error:
        raise ConflictException(detail=error)
    if "SALESFORCE_INBOX_TRANSPORT_UNKNOWN_ERROR" in error:
        raise ConflictException(detail=error)
    if "SELF_REFERENCE_FROM_TRIGGER" in error:
        raise ConflictException(detail=error)
    if "SHARE_NEEDED_FOR_CHILD_OWNER" in error:
        raise ConflictException(detail=error)
    if "SINGLE_EMAIL_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "SLACK_API_ERROR" in error:
        raise ConflictException(detail=error)
    if "SOCIAL_ACCOUNT_NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "SOCIAL_POST_INVALID" in error:
        raise ConflictException(detail=error)
    if "SOCIAL_POST_NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "STANDARD_PRICE_NOT_DEFINED" in error:
        raise ConflictException(detail=error)
    if "STORAGE_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "STRING_TOO_LONG" in error:
        raise ConflictException(detail=error)
    if "TABSET_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "TEMPLATE_NOT_ACTIVE" in error:
        raise ConflictException(detail=error)
    if "TERRITORY_REALIGN_IN_PROGRESS" in error:
        raise ConflictException(detail=error)
    if "TEXT_DATA_OUTSIDE_SUPPORTED_CHARSET" in error:
        raise ConflictException(detail=error)
    if "TEXT_TO_PICKLIST_VALUES_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "TOO_MANY_ENUM_VALUE" in error:
        raise ConflictException(detail=error)
    if "TOO_MANY_JOBS" in error:
        raise ConflictException(detail=error)
    if "TRANSFER_REQUIRES_READ" in error:
        raise ConflictException(detail=error)
    if "UISF_ENTITY_QUERY_FAILED" in error:
        raise ConflictException(detail=error)
    if "UISF_NO_MAPPINGS_FOUND" in error:
        raise ConflictException(detail=error)
    if "UISF_TOKEN_NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "UISF_UNKNOWN_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "UISF_USER_MAPPING_FAILED" in error:
        raise ConflictException(detail=error)
    if "UNAVAILABLE_REF" in error:
        raise ConflictException(detail=error)
    if "UNABLE_TO_LOCK_ROW" in error:
        raise ConflictException(detail=error)
    if "UNAVAILABLE_RECORDTYPE_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "UNDELETE_FAILED" in error:
        raise ConflictException(detail=error)
    if "DELETE_FAILED" in error:
        raise ConflictException(detail=error)
    if "UNKNOWN_EXCEPTION" in error:
        raise ConflictException(detail=error)
    if "UNQUALIFIED_CART" in error:
        raise ConflictException(detail=error)
    if "UNSPECIFIED_EMAIL_ADDRESS" in error:
        raise ConflictException(detail=error)
    if "UNSUPPORTED_APEX_TRIGGER_OPERATON" in error:
        raise ConflictException(detail=error)
    if "UNSUPPORTED_DML" in error:
        raise ConflictException(detail=error)
    if "UNSUPPORTED_MODE" in error:
        raise ConflictException(detail=error)
    if "UNSUPPORTED_PAYMENT_REQUEST_TYPE" in error:
        raise ConflictException(detail=error)
    if "UNSUPPORTED_QUERY" in error:
        raise ConflictException(detail=error)
    if "UNVERIFIED_SENDER_ADDRESS" in error:
        raise ConflictException(detail=error)
    if "USER_WITHOUT_WEM_PERMISSION" in error:
        raise ConflictException(detail=error)
    if "VARIANT_NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "VF_COMPILE_ERROR" in error:
        raise ConflictException(detail=error)
    if "WEBLINK_SIZE_LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "LIMIT_EXCEEDED" in error:
        raise ConflictException(detail=error)
    if "WEBLINK_URL_INVALID" in error:
        raise ConflictException(detail=error)
    if "WEM_USER_NOT_ORG_ADMIN" in error:
        raise ConflictException(detail=error)
    if "WORKSPACE_NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "WRONG_CONTROLLER_TYPE" in error:
        raise ConflictException(detail=error)

    # extendedErrorCode in salesforce error response
    if "FLOW_CANNOT_BE_REACTIVATED" in error:
        raise ConflictException(detail=error)
    if "FLOW_NOT_FOUND" in error:
        raise NotFoundException(detail=error)
    if "FLOW_TEST_CONDITION_INVALID_DATATYPE_MAPPING" in error:
        raise BadRequestException(detail=error)
    if "FLOW_TEST_INVALID_LHS_REFERENCE" in error:
        raise BadRequestException(detail=error)
    if "FLOW_TEST_NOT_SUPPORTED" in error:
        raise BadRequestException(detail=error)
    if "FLOW_TEST_PARAMETER_LEFTVALUEREFERENCE_INVALID" in error:
        raise BadRequestException(detail=error)
    if "FLOW_TEST_PARAMETER_TYPE_INVALID" in error:
        raise BadRequestException(detail=error)
    if "FLOW_TEST_PARAMETER_VALUE_INVALID" in error:
        raise BadRequestException(detail=error)
    if "FLOW_TEST_PARAMETER_VALUE_MISSING" in error:
        raise BadRequestException(detail=error)
    if "FLOW_TEST_PARAMS_REQUIRED" in error:
        raise BadRequestException(detail=error)
    if "FORM_ALREADY_IN_USE_BY_DRAFT_VERSION" in error:
        raise ConflictException(detail=error)
    if "FORM_ALREADY_IN_USE_BY_FLOW" in error:
        raise ConflictException(detail=error)
    if "INVALID_QUERY_LOCATOR_FORMAT" in error:
        raise BadRequestException(detail=error)
    if "INVALID_QUERY_LOCATOR" in error:
        raise ConflictException(detail=error)
    if "INVALID_SEGMENT_STATUS_FOR_ACTIVATION" in error:
        raise BadRequestException(detail=error)
    if "LOCATOR_LOCATION_EXCEEDS_SIZE" in error:
        raise BadRequestException(detail=error)
    if "MAX_STATEMENT_SIZE" in error:
        raise BadRequestException(detail=error)
    if "MAX_XDS_IMPLICIT_SUBQUERIES" in error:
        raise BadRequestException(detail=error)
    if "PROGRAM_PROGRESS_NOT_ACTIVE" in error:
        raise BadRequestException(detail=error)
    if "QUERY_LOCATOR_EXPIRED" in error:
        raise BadRequestException(detail=error)
    if "QUERY_LOCATOR_NOT_FOUND" in error:
        raise BadRequestException(detail=error)
    if "NOT_FOUND" in error:
        raise ConflictException(detail=error)
    if "SCREENFIELD_OBJECTPROVIDED_INVALID_DATATYPE" in error:
        raise BadRequestException(detail=error)
    if "SURVEY_INVALID_MATRIX_QUESTION_CONFIGURATION" in error:
        raise BadRequestException(detail=error)
    if "TEMPORARY_QUERY_MORE_FAILURE" in error:
        raise BadRequestException(detail=error)
    if "UNAUTHORIZED_USER_FOR_CURSOR" in error:
        raise BadRequestException(detail=error)

    raise BadRequestException(detail=error)


def create_salesforce_company(
    db: Session,
    sync_log_history: SalesforceSyncHistories,
    ss_company_corporate_number: str,
):
    salesforce_connection = db.exec(
        select(SalesforceIntegrations).where(
            SalesforceIntegrations.team_id == sync_log_history.team_id,
            SalesforceIntegrations.deleted_at.is_(None),
        )
    ).first()

    if not salesforce_connection:
        raise NotFoundException(detail="integration.salesforce.notFoundConnection")

    ss_company = db.exec(
        select(Company).where(Company.corporate_number == ss_company_corporate_number)
    ).first()

    if not ss_company:
        raise NotFoundException(detail="common.notFoundCompany")

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
            SalesforceCompanyFieldMappings.team_id == salesforce_connection.team_id,
            SalesforceCompanyFieldMappings.deleted_at.is_(None),
        )
    ).all()

    salesforce_service = SalesforceService(
        access_token=salesforce_connection.access_token,
        refresh_token=salesforce_connection.refresh_token,
        instance_url=salesforce_connection.instance_url,
        id_url=salesforce_connection.id_url,
    )

    properties = {}
    for mapping in field_mappings:
        field_value = None
        if mapping.field == "nta_city_id":
            field_value = company_city if company_city else None
        elif mapping.field == "nta_prefecture_id":
            field_value = company_prefecture if company_prefecture else None
        elif mapping.field == "establish_at":
            field_value = (
                str(ss_company.establish_at.year) if ss_company.establish_at else None
            )
        elif mapping.field == "domain" and ss_company.domain:
            domain_value = getattr(ss_company, mapping.field, "")
            field_value = validate_and_clean_domain(domain_value)
        elif mapping.field == "industry_code" and ss_company.industry_code is not None:
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
        try:
            new_salesforce_company = salesforce_service.create_company(properties)
            return new_salesforce_company.get("id")
        except HTTPException as e:
            print("_______ error create salesforce company in batch _______")
            raise_exception_salesforce(e)
