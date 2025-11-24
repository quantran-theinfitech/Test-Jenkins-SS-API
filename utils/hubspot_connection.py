import json
from typing import List, Optional, Union

import requests
from fastapi import HTTPException
from hubspot import HubSpot
from hubspot.crm.companies import ApiException as CompanyApiException
from hubspot.crm.companies import (
    Filter,
    FilterGroup,
    PublicObjectSearchRequest,
    SimplePublicObjectInput,
    SimplePublicObjectInputForCreate,
)
from hubspot.crm.contacts import ApiException as ContactApiException
from sqlmodel import Session, select

from app.api.base.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    TooManyRequestsException,
)
from app.config import settings
from app.constant.constants import INDUSTRIES_CATEGORIES, LISTING_MARKET_CODE
from app.models.city import City
from app.models.company import Company
from app.models.integration.hubspot.hubspot_company_field_mappings import (
    HubspotCompanyFieldMappings,
)
from app.models.integration.hubspot.hubspot_company_sync_histories import (
    HubspotCompanySyncHistories,
)
from app.models.integration.hubspot.hubspot_integrations import HubspotIntergrations
from app.models.prefecture import Prefecture
from utils.extension import validate_and_clean_domain


class HubSpotService:
    def __init__(self, access_token, refresh_token=None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client = HubSpot(access_token=self.access_token)

    def refresh_client(self):
        try:
            auth_data = {
                "grant_type": "refresh_token",
                "client_id": settings.HUBSPOT_CLIENT_ID,
                "client_secret": settings.HUBSPOT_CLIENT_SECRET,
                "refresh_token": self.refresh_token,
            }
            response = requests.post(settings.HUBSPOT_HOST, data=auth_data)
            response_data = response.json()
            if response.status_code != 200:
                error = str(response_data)
                print(
                    f"ErrorRefreshingHubSpot(StatusCode:{response.status_code}):{error}"
                )
                raise BadRequestException(detail=error)

            self.access_token = response_data["access_token"]
            self.client = HubSpot(access_token=self.access_token)
        except HTTPException as e:
            print("_______ error refresh_client _______", str(e))
            raise e

    def get_user_info(self):
        self.refresh_client()
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            user_info_response = requests.get(
                f"https://api.hubapi.com/oauth/v1/access-tokens/{self.access_token}",
                headers=headers,
            )
            return json.loads(user_info_response.text)
        except HTTPException as e:
            print(f"Failed to get user info: {str(e)}")
            raise BadRequestException(detail=str(e))

    def get_schema_company(self):
        self.refresh_client()
        try:
            company_properties = self.client.crm.properties.core_api.get_all(
                object_type="companies"
            )
            return company_properties.results
        except CompanyApiException as e:
            if e.status == 429:
                raise TooManyRequestsException(
                    detail="integration.hubspot.errorLog.tooManyRequests"
                )
            else:
                error_message = f"Failed to get company schema: {str(e)}"
                print(error_message)
                catch_error_hubspot(e)

    def get_all_contacts(self, properties: Optional[List[str]] = None):
        self.refresh_client()
        try:
            contacts = self.client.crm.contacts.get_all(properties=properties)
            return contacts
        except ContactApiException as e:
            if e.status == 429:
                raise TooManyRequestsException(
                    detail="integration.hubspot.errorLog.tooManyRequests"
                )
            else:
                error_message = f"Failed to get all contacts: {str(e)}"
                print(error_message)
                catch_error_hubspot(e)

    def get_all_companies(self, properties: Optional[List[str]] = None):
        self.refresh_client()
        try:
            companies = self.client.crm.companies.get_all(properties=properties)
            return companies
        except CompanyApiException as e:
            if e.status == 429:
                raise TooManyRequestsException(
                    detail="integration.hubspot.errorLog.tooManyRequests"
                )
            else:
                error_message = f"Failed to get all company: {str(e)}"
                print(error_message)
                catch_error_hubspot(e)

    def get_nocompany_contacts(self):
        self.refresh_client()
        try:
            filter = Filter(
                property_name="associatedcompanyid", operator="NOT_HAS_PROPERTY"
            )
            filter_group = FilterGroup(filters=[filter])
            search_request = PublicObjectSearchRequest(
                filter_groups=[filter_group], limit=200
            )
            contacts_results = []

            while True:
                contacts = self.client.crm.contacts.search_api.do_search(search_request)

                if contacts.results and len(contacts.results) > 0:
                    contacts_results.extend(contacts.results)

                if not contacts.paging or not contacts.paging.next:
                    break

                search_request.after = contacts.paging.next.after

            return contacts_results
        except ContactApiException as e:
            if e.status == 429:
                raise TooManyRequestsException(
                    detail="integration.hubspot.errorLog.tooManyRequests"
                )
            else:
                error_message = f"Failed to get contacts without company: {str(e)}"
                print(error_message)
                catch_error_hubspot(e)

    def create_company(self, properties: dict):
        self.refresh_client()
        try:
            company = self.client.crm.companies.basic_api.create(
                SimplePublicObjectInputForCreate(properties=properties)
            )
            return company
        except CompanyApiException as e:
            if e.status == 429:
                raise TooManyRequestsException(
                    detail="integration.hubspot.errorLog.tooManyRequests"
                )
            else:
                error_message = f"Failed to create company: {str(e)}"
                print(error_message)
                catch_error_hubspot(e)

    def search_company_hubpsot(
        self, keyword: str, limit: int = 10, after: Optional[str] = None
    ):
        """
        Search companies in Hubspot by keyword
        Args:
            keyword: Search keyword
            limit: Number of results to return (default: 10, max: 100)
            after: Pagination token for next page
        Returns:
            Hubspot companies search results
        Raises:
            ValueError: When input parameters are invalid
            CompanyApiException: When Hubspot API call fails
        """
        # Validate input parameters
        if not keyword or not keyword.strip():
            raise ValueError("Search keyword cannot be empty")

        if not isinstance(limit, int) or limit < 1 or limit > 100:
            raise ValueError("Limit must be an integer between 1 and 100")

        self.refresh_client()

        # Create filters for different company properties
        filters = [
            Filter(property_name="name", operator="CONTAINS_TOKEN", value=keyword),
            Filter(property_name="domain", operator="CONTAINS_TOKEN", value=keyword),
            Filter(property_name="address", operator="CONTAINS_TOKEN", value=keyword),
            Filter(property_name="phone", operator="CONTAINS_TOKEN", value=keyword),
            Filter(property_name="industry", operator="CONTAINS_TOKEN", value=keyword),
        ]

        # Create filter groups for OR condition
        filter_groups = [FilterGroup(filters=[filter]) for filter in filters]

        # Define properties to return
        properties = [
            "name",
            "domain",
            "address",
            "phone",
            "industry",
            "website",
            "createdate",
            "lastactivitydate",
            "numberofemployees",
            "annualrevenue",
            "type",
            "description",
            "city",
            "state",
            "country",
        ]

        # Create search request
        search_request = PublicObjectSearchRequest(
            filter_groups=filter_groups,
            sorts=[{"propertyName": "name", "direction": "ASCENDING"}],
            limit=limit,
            after=after,
            properties=properties,
        )

        try:
            companies = self.client.crm.companies.search_api.do_search(
                public_object_search_request=search_request
            )
            return companies
        except CompanyApiException as e:
            if e.status == 429:
                raise TooManyRequestsException(
                    detail="integration.hubspot.errorLog.tooManyRequests"
                )
            else:
                error_message = f"Failed to search companies in Hubspot: {str(e)}"
                print(error_message)
                catch_error_hubspot(e)

    def get_company_by_id(
        self,
        hubspot_company_id: str,
        properties: Optional[List[str]] = ["name", "domain"],
    ):
        self.refresh_client()
        try:
            company = self.client.crm.companies.basic_api.get_by_id(
                company_id=hubspot_company_id, properties=properties
            )
            return company
        except CompanyApiException as e:
            if e.status == 404:
                raise NotFoundException(
                    detail="integration.hubspot.errorLog.notFoundCompanyInHubspot"
                )
            elif e.status == 429:
                raise TooManyRequestsException(
                    detail="integration.hubspot.errorLog.tooManyRequests"
                )
            else:
                print(f"Exception when calling HubSpot API: {e}")
                catch_error_hubspot(e)

    def get_person_by_id(self, hubspot_person_id: str):
        self.refresh_client()
        try:
            company = self.client.crm.contacts.basic_api.get_by_id(
                contact_id=hubspot_person_id, associations=["company"]
            )
            return company
        except ContactApiException as e:
            if e.status == 404:
                raise NotFoundException(
                    detail="integration.hubspot.errorLog.notFoundPersonInHubspot"
                )
            elif e.status == 429:
                raise TooManyRequestsException(
                    detail="integration.hubspot.errorLog.tooManyRequests"
                )
            else:
                print(f"Exception when calling HubSpot API: {e}")
                catch_error_hubspot(e)

    def update_company(self, company_id, properties):
        self.refresh_client()
        try:
            simple_public_object_input = SimplePublicObjectInput(properties=properties)
            response = self.client.crm.companies.basic_api.update(
                company_id, simple_public_object_input
            )
            return response
        except CompanyApiException as e:
            if e.status == 429:
                raise TooManyRequestsException(
                    detail="integration.hubspot.errorLog.tooManyRequests"
                )
            else:
                error_message = f"Failed to update company: {str(e)}"
                print(error_message)
                catch_error_hubspot(e)

    def update_person_association_id(self, person_id, association_id):
        self.refresh_client()
        try:
            self.client.crm.associations.v4.basic_api.create_default(
                from_object_type="contact",
                from_object_id=person_id,
                to_object_id=association_id,
                to_object_type="company",
            )
        except ContactApiException as e:
            if e.status == 429:
                raise TooManyRequestsException(
                    detail="integration.hubspot.errorLog.tooManyRequests"
                )
            else:
                error_message = f"Failed to update person association ID: {str(e)}"
                print(error_message)
                catch_error_hubspot(e)

    def create_custom_field(
        self,
        name: str,
        label: str,
        type: str = "string",
        field_type: str = "text",
        group_name: str = "companyinformation",
        object_type: str = "companies",
    ):
        self.refresh_client()
        try:
            property_create = {
                "name": name,
                "label": label,
                "type": type,
                "fieldType": field_type,
                "groupName": group_name,
            }

            if type == "bool":
                property_create["fieldType"] = "booleancheckbox"
                property_create["options"] = [
                    {"label": "Yes", "value": True, "displayOrder": 0},
                    {"label": "No", "value": False, "displayOrder": 1},
                ]

            custom_field = self.client.crm.properties.core_api.create(
                object_type=object_type,
                property_create=property_create,
            )

            return custom_field
        except CompanyApiException:
            raise
        except HTTPException as e:
            if str(e).find("OBJECT_ALREADY_EXISTS") != -1:
                raise ConflictException(
                    detail="integration.hubspot.customField.duplicateName"
                )
            else:
                print(f"Failed to create custom field: {str(e)}")
                catch_error_hubspot(e)


def get_token_hubspot(code: str):
    auth_data = {
        "grant_type": "authorization_code",
        "redirect_uri": settings.REDIRECT_URI,
        "client_id": settings.HUBSPOT_CLIENT_ID,
        "client_secret": settings.HUBSPOT_CLIENT_SECRET,
        "code": code,
    }
    response = requests.post(settings.HUBSPOT_HOST, data=auth_data)
    if response.status_code != 200:
        print("_______ settings.REDIRECT_URI _______", settings.REDIRECT_URI)
        print("_______ response.json() _______", response.json())
        raise ConflictException(detail="integration.hubspot.connectFailed")

    response_data = response.json()
    return response_data["access_token"], response_data["refresh_token"]


def catch_error_hubspot(
    e: Union[HTTPException, Exception, CompanyApiException, ContactApiException]
):
    print("Vars:", vars(e))
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
    print("_______ error catch_error_hubspot _______", error)
    raise BadRequestException(detail=str(error))


def create_hubspot_company(
    db: Session,
    sync_log_history: HubspotCompanySyncHistories,
    ss_company_corporate_number: str,
):
    hubspot_connection = db.exec(
        select(HubspotIntergrations).where(
            HubspotIntergrations.team_id == sync_log_history.team_id,
            HubspotIntergrations.deleted_at.is_(None),
        )
    ).first()

    if not hubspot_connection:
        raise NotFoundException(detail="integration.hubspot.notFoundConnection")

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

    hubspot_service = HubSpotService(
        access_token=hubspot_connection.access_token,
        refresh_token=hubspot_connection.refresh_token,
    )

    field_mappings = db.exec(
        select(HubspotCompanyFieldMappings).where(
            HubspotCompanyFieldMappings.integration_id == hubspot_connection.id,
            HubspotCompanyFieldMappings.hubspot_team_id
            == hubspot_connection.hubspot_team_id,
        )
    ).all()

    properties = {}
    for field in field_mappings:
        field_value = None
        if field.field == "nta_city_id":
            field_value = company_city if company_city else None
        elif field.field == "nta_prefecture_id":
            field_value = company_prefecture if company_prefecture else None
        elif field.field == "establish_at":
            field_value = (
                str(ss_company.establish_at.year) if ss_company.establish_at else None
            )
        elif field.field == "domain" and ss_company.domain:
            domain_value = getattr(ss_company, field.field, "")
            field_value = validate_and_clean_domain(domain_value)
        elif field.field == "industry_code" and ss_company.industry_code is not None:
            field_value = INDUSTRIES_CATEGORIES[ss_company.industry_code]["text"]
        elif (
            field.field == "main_sub_industry_code"
            and ss_company.main_sub_industry_code is not None
        ):
            for industry in INDUSTRIES_CATEGORIES.values():
                for child in industry.get("child", []):
                    if child["code"] == ss_company.main_sub_industry_code:
                        field_value = child["text"]
                        break
        elif (
            field.field == "listing_market_code"
            and ss_company.listing_market_code is not None
        ):
            field_value = LISTING_MARKET_CODE[ss_company.listing_market_code]
        elif field.field == "is_listed_market":
            field_value = (
                getattr(ss_company, "listing_market_code", None) is not None
                and getattr(ss_company, "listing_market_code", None) != "UNLISTED"
            )
        else:
            field_value = (
                getattr(ss_company, field.field, None) if field.field else None
            )

        if field_value:
            properties[field.hubspot_field] = field_value

    if properties:
        try:
            new_hubspot_company = hubspot_service.create_company(properties)
            return new_hubspot_company.id
        except HTTPException as e:
            catch_error_hubspot(e)
