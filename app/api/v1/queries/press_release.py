from typing import List

from elasticsearch_dsl import Q

from app.api.v1.queries.cross import (
    _filter_by_posted_at_es_query,
    _search_by_average_age_es_query,
    _search_by_business_model_codes_es_query,
    _search_by_capital_es_query,
    _search_by_closing_month_es_query,
    _search_by_cloud_services_es_query,
    _search_by_communication_tools_es_query,
    _search_by_company_collections_es_query,
    _search_by_company_identified_es_query,
    _search_by_company_keyword_es_query,
    _search_by_company_name_es_query,
    _search_by_contact_information_es_query,
    _search_by_corporate_numbers_es_query,
    _search_by_domain_name_es_query,
    _search_by_establish_at_es_query,
    _search_by_exact_company_keyword_es_query,
    _search_by_exclude_corporate_numbers_es_query,
    _search_by_framework_technologies_es_query,
    _search_by_funding_es_query,
    _search_by_industries_es_query,
    _search_by_job_update_date_es_query,
    _search_by_language_technologies_es_query,
    _search_by_listed_exchanges_es_query,
    _search_by_listing_division_es_query,
    _search_by_locations_es_query,
    _search_by_management_tools_es_query,
    _search_by_marketing_tools_es_query,
    _search_by_number_of_employees_es_query,
    _search_by_original_tags_es_query,
    _search_by_other_tools_es_query,
    _search_by_revenue_es_query,
    build_press_release_es_query,
)
from app.api.v1.schemas.search_cross import (
    SearchCompanyRequest,
    SearchCrossRequest,
    SearchMode,
)
from utils.extract_domain import (
    normalized_domain_search_companies,
    normalized_sns_url_search_persons,
    split_string_by_newline,
)


def build_es_query(
    request: SearchCrossRequest,
    corporate_numbers_downloaded: List[str] = [],
    corporate_numbers_by_tags: List[str] = [],
    business_categories: List[str] = [],
):
    query = []
    query.append(_filter_by_posted_at_es_query(False))
    if request.new_press_release:
        press_release_query = build_press_release_es_query(
            request.new_press_release, False, business_categories
        )
        if len(press_release_query) > 0:
            query.append(Q("bool", must=press_release_query))
    company_query = _build_company_es_query(
        request, corporate_numbers_downloaded, corporate_numbers_by_tags
    )
    if len(company_query) > 0:
        query.append(Q("bool", must=Q("bool", must=company_query)))

    return Q("bool", must=query)


def _build_company_es_query(
    request: SearchCompanyRequest,
    corporate_numbers_downloaded: List[str] = [],
    corporate_numbers_by_tags: List[str] = [],
):
    request = normalized_sns_url_search_persons(
        normalized_domain_search_companies(request)
    )
    must_queries = []
    if request.company_keywords:
        if request.company_keywords.is_exact:
            must_queries.extend(
                _search_by_exact_company_keyword_es_query(
                    search=request.company_keywords,
                    is_nested=True,
                    mode=SearchMode.EXACT,
                )
            )
        else:
            must_queries.extend(
                _search_by_company_keyword_es_query(
                    search=request.company_keywords,
                    is_nested=True,
                    mode=SearchMode.EXACT,
                )
            )

    if request.industries:
        must_queries.append(
            _search_by_industries_es_query(request.industries, True, SearchMode.EXACT)
        )

    if request.locations:
        must_queries.append(
            _search_by_locations_es_query(request.locations, True, SearchMode.EXACT)
        )

    if request.company_name:
        must_queries.extend(
            _search_by_company_name_es_query(
                split_string_by_newline(request.company_name), True, SearchMode.EXACT
            )
        )

    if request.domain_name:
        must_queries.extend(
            _search_by_domain_name_es_query(request.domain_name, True, SearchMode.EXACT)
        )
    if request.date_of_establishment:
        must_queries.extend(
            _search_by_establish_at_es_query(
                request.date_of_establishment, True, SearchMode.EXACT
            )
        )
    if request.closing_month:
        must_queries.extend(
            _search_by_closing_month_es_query(
                request.closing_month, True, SearchMode.EXACT
            )
        )

    if request.listing_division:
        must_queries.extend(
            _search_by_listing_division_es_query(
                request.listing_division, True, SearchMode.EXACT
            )
        )

    if request.listed_exchanges:
        must_queries.append(
            _search_by_listed_exchanges_es_query(
                request.listed_exchanges, True, SearchMode.EXACT
            )
        )

    if request.average_age:
        must_queries.extend(
            _search_by_average_age_es_query(request.average_age, True, SearchMode.EXACT)
        )

    if request.marketing_tools:
        must_queries.extend(
            _search_by_marketing_tools_es_query(
                request.marketing_tools, True, SearchMode.EXACT
            )
        )

    if request.communication_tools:
        must_queries.extend(
            _search_by_communication_tools_es_query(
                request.communication_tools, True, SearchMode.EXACT
            )
        )
    if request.management_tools:
        must_queries.extend(
            _search_by_management_tools_es_query(
                request.management_tools, True, SearchMode.EXACT
            )
        )

    if request.other_tools:
        must_queries.extend(
            _search_by_other_tools_es_query(request.other_tools, True, SearchMode.EXACT)
        )

    if request.language_technologies:
        must_queries.extend(
            _search_by_language_technologies_es_query(
                request.language_technologies, True, SearchMode.EXACT
            )
        )

    if request.framework_technologies:
        must_queries.extend(
            _search_by_framework_technologies_es_query(
                request.framework_technologies, True, SearchMode.EXACT
            )
        )

    if request.cloud_services:
        must_queries.extend(
            _search_by_cloud_services_es_query(
                request.cloud_services, True, SearchMode.EXACT
            )
        )

    if request.number_of_employees:
        must_queries.extend(
            _search_by_number_of_employees_es_query(
                request.number_of_employees, True, SearchMode.EXACT
            )
        )

    if request.capital:
        must_queries.extend(
            _search_by_capital_es_query(request.capital, True, SearchMode.EXACT)
        )

    if request.revenue:
        must_queries.append(
            _search_by_revenue_es_query(request.revenue, True, SearchMode.EXACT)
        )

    if request.job_update_date:
        must_queries.append(
            _search_by_job_update_date_es_query(
                request.job_update_date, True, SearchMode.EXACT
            )
        )

    if request.contact_information:
        must_queries.append(
            _search_by_contact_information_es_query(
                request.contact_information, True, SearchMode.EXACT
            )
        )

    if request.business_models:
        must_queries.extend(
            _search_by_business_model_codes_es_query(
                request.business_models, True, SearchMode.EXACT
            )
        )

    if request.corporate_numbers:
        must_queries.append(
            _search_by_corporate_numbers_es_query(
                request.corporate_numbers, True, SearchMode.EXACT
            )
        )

    if request.exclude_corporate_numbers:
        must_queries.append(
            _search_by_exclude_corporate_numbers_es_query(
                request.exclude_corporate_numbers,
                False,
                SearchMode.EXACT,
            )
        )

    if request.is_companies_unlocked:
        if len(corporate_numbers_downloaded) >= 0:
            must_queries.append(
                _search_by_corporate_numbers_es_query(
                    corporate_numbers_downloaded, True, SearchMode.EXACT
                )
            )

    if request.corporate_numbers_by_collection:
        must_queries.extend(
            _search_by_company_collections_es_query(
                request.corporate_numbers_by_collection,
                request.company_collections,
                True,
                SearchMode.EXACT,
            )
        )

    if request.corporate_numbers_identified:
        must_queries.extend(
            _search_by_company_identified_es_query(
                request.corporate_numbers_identified, True, SearchMode.EXACT
            )
        )
    if request.funding:
        must_queries.append(
            _search_by_funding_es_query(request.funding, True, SearchMode.EXACT)
        )

    if request.original_tags:
        must_queries.append(
            _search_by_original_tags_es_query(
                request.original_tags, True, SearchMode.EXACT
            )
        )

    if request.tags:
        must_queries.append(
            _search_by_corporate_numbers_es_query(
                corporate_numbers_by_tags, True, SearchMode.EXACT
            )
        )

    return must_queries
