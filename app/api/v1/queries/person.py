from typing import List

from elasticsearch_dsl import Q

from app.api.v1.queries.cross import (
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
    _search_by_exact_person_keyword_es_query,
    _search_by_exclude_corporate_numbers_es_query,
    _search_by_framework_technologies_es_query,
    _search_by_funding_es_query,
    _search_by_industries_es_query,
    _search_by_job_update_date_es_query,
    _search_by_keyword_es_query,
    _search_by_language_technologies_es_query,
    _search_by_listed_exchanges_es_query,
    _search_by_listing_division_es_query,
    _search_by_locations_es_query,
    _search_by_management_tools_es_query,
    _search_by_marketing_tools_es_query,
    _search_by_name_es_query,
    _search_by_number_of_employees_es_query,
    _search_by_opt_out_es_query,
    _search_by_original_tags_es_query,
    _search_by_other_tools_es_query,
    _search_by_person_collections_es_query,
    _search_by_person_keyword_es_query,
    _search_by_platform_es_query,
    _search_by_press_release_es_query,
    _search_by_revenue_es_query,
    _search_by_role_code_es_query,
    _search_by_role_code_groups_es_query,
    _search_by_sns_urls_es_query,
    _search_by_uuid_es_query,
)
from app.api.v1.schemas.search_cross import SearchCrossRequest, SearchMode
from utils.extract_domain import split_string_by_newline
from utils.optimize_name import optimize_name, translate_roles


def build_es_query(
    request: SearchCrossRequest,
    persons_uuids: List[str] = [],
    persons_csv_uuids: List[str] = [],
    corporate_numbers_downloaded: List[str] = [],
    corporate_numbers_by_tags: List[str] = [],
    is_unlimited_account: bool = False,
):
    person_queries = []
    company_queries = []
    company_fuzzy_queries = []

    if request.person_keywords:
        if request.person_keywords.is_exact:
            person_queries.extend(
                _search_by_exact_person_keyword_es_query(request.person_keywords, False)
            )
        else:
            person_queries.extend(
                _search_by_person_keyword_es_query(request.person_keywords, False)
            )

    if request.company_keywords:
        if request.company_keywords.is_exact:
            company_queries.extend(
                _search_by_exact_company_keyword_es_query(
                    search=request.company_keywords,
                    is_nested=True,
                    mode=SearchMode.EXACT,
                )
            )
            company_fuzzy_queries.extend(
                _search_by_exact_company_keyword_es_query(
                    search=request.company_keywords,
                    is_nested=True,
                    mode=SearchMode.FUZZY,
                )
            )
        else:
            company_queries.extend(
                _search_by_company_keyword_es_query(
                    search=request.company_keywords,
                    is_nested=True,
                    mode=SearchMode.EXACT,
                )
            )
            company_fuzzy_queries.extend(
                _search_by_company_keyword_es_query(
                    search=request.company_keywords,
                    is_nested=True,
                    mode=SearchMode.FUZZY,
                )
            )

    if request.keyword:
        company_queries.append(
            _search_by_keyword_es_query(
                optimize_name(request.keyword), True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.append(
            _search_by_keyword_es_query(
                optimize_name(request.keyword), True, SearchMode.FUZZY
            )
        )

    if request.industries:
        company_queries.append(
            _search_by_industries_es_query(request.industries, True, SearchMode.EXACT)
        )
        company_fuzzy_queries.append(
            _search_by_industries_es_query(request.industries, True, SearchMode.FUZZY)
        )
    if request.locations:
        company_queries.append(
            _search_by_locations_es_query(request.locations, True, SearchMode.EXACT)
        )
        company_fuzzy_queries.append(
            _search_by_locations_es_query(request.locations, True, SearchMode.FUZZY)
        )
    if request.company_name:
        company_queries.extend(
            _search_by_company_name_es_query(
                split_string_by_newline(request.company_name), True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.extend(
            _search_by_company_name_es_query(
                split_string_by_newline(request.company_name), True, SearchMode.FUZZY
            )
        )
    if request.domain_name:
        company_queries.extend(
            _search_by_domain_name_es_query(
                split_string_by_newline(request.domain_name), True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.extend(
            _search_by_domain_name_es_query(
                split_string_by_newline(request.domain_name), True, SearchMode.FUZZY
            )
        )
    if request.date_of_establishment:
        company_queries.extend(
            _search_by_establish_at_es_query(
                request.date_of_establishment, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.extend(
            _search_by_establish_at_es_query(
                request.date_of_establishment, True, SearchMode.FUZZY
            )
        )
    if request.closing_month:
        company_queries.extend(
            _search_by_closing_month_es_query(
                request.closing_month, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.extend(
            _search_by_closing_month_es_query(
                request.closing_month, True, SearchMode.FUZZY
            )
        )
    if request.listing_division:
        company_queries.extend(
            _search_by_listing_division_es_query(
                request.listing_division, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.extend(
            _search_by_listing_division_es_query(
                request.listing_division, True, SearchMode.FUZZY
            )
        )
    if request.listed_exchanges:
        company_queries.append(
            _search_by_listed_exchanges_es_query(
                request.listed_exchanges, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.append(
            _search_by_listed_exchanges_es_query(
                request.listed_exchanges, True, SearchMode.FUZZY
            )
        )
    if request.average_age:
        company_queries.extend(
            _search_by_average_age_es_query(request.average_age, True, SearchMode.EXACT)
        )
        company_fuzzy_queries.extend(
            _search_by_average_age_es_query(request.average_age, True, SearchMode.FUZZY)
        )
    if request.press_release:
        company_queries.extend(
            _search_by_press_release_es_query(
                request.press_release, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.extend(
            _search_by_press_release_es_query(
                request.press_release, True, SearchMode.FUZZY
            )
        )
    if request.marketing_tools:
        company_queries.extend(
            _search_by_marketing_tools_es_query(
                request.marketing_tools, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.extend(
            _search_by_marketing_tools_es_query(
                request.marketing_tools, True, SearchMode.FUZZY
            )
        )
    if request.communication_tools:
        company_queries.extend(
            _search_by_communication_tools_es_query(
                request.communication_tools, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.extend(
            _search_by_communication_tools_es_query(
                request.communication_tools, True, SearchMode.FUZZY
            )
        )
    if request.management_tools:
        company_queries.extend(
            _search_by_management_tools_es_query(
                request.management_tools, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.extend(
            _search_by_management_tools_es_query(
                request.management_tools, True, SearchMode.FUZZY
            )
        )
    if request.other_tools:
        company_queries.extend(
            _search_by_other_tools_es_query(request.other_tools, True, SearchMode.EXACT)
        )
        company_fuzzy_queries.extend(
            _search_by_other_tools_es_query(request.other_tools, True, SearchMode.FUZZY)
        )
    if request.language_technologies:
        company_queries.extend(
            _search_by_language_technologies_es_query(
                request.language_technologies, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.extend(
            _search_by_language_technologies_es_query(
                request.language_technologies, True, SearchMode.FUZZY
            )
        )
    if request.framework_technologies:
        company_queries.extend(
            _search_by_framework_technologies_es_query(
                request.framework_technologies, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.extend(
            _search_by_framework_technologies_es_query(
                request.framework_technologies, True, SearchMode.FUZZY
            )
        )
    if request.cloud_services:
        company_queries.extend(
            _search_by_cloud_services_es_query(
                request.cloud_services, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.extend(
            _search_by_cloud_services_es_query(
                request.cloud_services, True, SearchMode.FUZZY
            )
        )
    if request.number_of_employees:
        company_queries.extend(
            _search_by_number_of_employees_es_query(
                request.number_of_employees, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.extend(
            _search_by_number_of_employees_es_query(
                request.number_of_employees, True, SearchMode.FUZZY
            )
        )
    if request.capital:
        company_queries.extend(
            _search_by_capital_es_query(request.capital, True, SearchMode.EXACT)
        )
        company_fuzzy_queries.extend(
            _search_by_capital_es_query(request.capital, True, SearchMode.FUZZY)
        )
    if request.revenue:
        company_queries.append(
            _search_by_revenue_es_query(request.revenue, True, SearchMode.EXACT)
        )
        company_fuzzy_queries.append(
            _search_by_revenue_es_query(request.revenue, True, SearchMode.FUZZY)
        )
    if request.job_update_date:
        company_queries.append(
            _search_by_job_update_date_es_query(
                request.job_update_date, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.extend(
            _search_by_job_update_date_es_query(
                request.job_update_date, True, SearchMode.FUZZY
            )
        )
    if request.contact_information:
        company_queries.append(
            _search_by_contact_information_es_query(
                request.contact_information, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.append(
            _search_by_contact_information_es_query(
                request.contact_information, True, SearchMode.FUZZY
            )
        )
    if request.business_models:
        company_queries.extend(
            _search_by_business_model_codes_es_query(
                request.business_models, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.extend(
            _search_by_business_model_codes_es_query(
                request.business_models, True, SearchMode.FUZZY
            )
        )
    if request.name:
        name_queries = _search_by_name_es_query(
            split_string_by_newline(request.name), False
        )
        person_queries.append(Q("bool", should=name_queries, minimum_should_match=1))

    if request.role_codes:
        person_queries.append(_search_by_role_code_es_query(request.role_codes, False))
    if request.role_group_codes:
        person_queries.append(
            _search_by_role_code_groups_es_query(
                translate_roles(request.role_group_codes), False
            )
        )
    if request.sns_url:
        person_queries.append(
            _search_by_sns_urls_es_query(
                split_string_by_newline(request.sns_url), False
            )
        )
    if request.corporate_numbers:
        company_queries.append(
            _search_by_corporate_numbers_es_query(
                request.corporate_numbers, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.append(
            _search_by_corporate_numbers_es_query(
                request.corporate_numbers, True, SearchMode.FUZZY
            )
        )
    if request.exclude_corporate_numbers:
        person_queries.append(
            _search_by_exclude_corporate_numbers_es_query(
                request.exclude_corporate_numbers,
                False,
                SearchMode.EXACT,
            )
        )
        company_fuzzy_queries.append(
            _search_by_exclude_corporate_numbers_es_query(
                request.exclude_corporate_numbers,
                True,
                SearchMode.FUZZY,
            )
        )
    if request.platform:
        person_queries.append(_search_by_platform_es_query(request.platform, False))
    if request.original_tags:
        company_queries.append(
            _search_by_original_tags_es_query(
                request.original_tags, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.append(
            _search_by_original_tags_es_query(
                request.original_tags, True, SearchMode.FUZZY
            )
        )
    if request.tags:
        company_queries.append(
            _search_by_corporate_numbers_es_query(
                corporate_numbers_by_tags, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.append(
            _search_by_corporate_numbers_es_query(
                corporate_numbers_by_tags, True, SearchMode.FUZZY
            )
        )
    if request.is_persons_unlocked and not is_unlimited_account:
        if len(persons_uuids) >= 0:
            person_queries.append(_search_by_uuid_es_query(persons_uuids, False))

    if request.is_companies_unlocked and not is_unlimited_account:
        if len(corporate_numbers_downloaded) >= 0:
            company_queries.append(
                _search_by_corporate_numbers_es_query(
                    corporate_numbers_downloaded, True, SearchMode.EXACT
                )
            )
            company_fuzzy_queries.append(
                _search_by_corporate_numbers_es_query(
                    corporate_numbers_downloaded, True, SearchMode.FUZZY
                )
            )

    if len(persons_csv_uuids) > 0:
        person_queries.append(_search_by_uuid_es_query(persons_csv_uuids, False))

    if request.corporate_numbers_by_collection:
        company_queries.extend(
            _search_by_company_collections_es_query(
                request.corporate_numbers_by_collection,
                request.company_collections,
                True,
                SearchMode.EXACT,
            )
        )
        company_fuzzy_queries.extend(
            _search_by_company_collections_es_query(
                request.corporate_numbers_by_collection,
                request.company_collections,
                True,
                SearchMode.FUZZY,
            )
        )
    if request.corporate_numbers_identified:
        company_queries.extend(
            _search_by_company_identified_es_query(
                request.corporate_numbers_identified, True, SearchMode.EXACT
            )
        )
        company_fuzzy_queries.extend(
            _search_by_company_identified_es_query(
                request.corporate_numbers_identified, True, SearchMode.FUZZY
            )
        )
    if request.uuids_by_collection:
        person_queries.extend(
            _search_by_person_collections_es_query(
                request.uuids_by_collection,
                request.person_collections,
                False,
            )
        )
    if request.person_uuids:
        person_queries.append(_search_by_uuid_es_query(request.person_uuids, False))

    if request.funding:
        company_queries.append(
            _search_by_funding_es_query(request.funding, True, SearchMode.EXACT)
        )
        company_fuzzy_queries.append(
            _search_by_funding_es_query(request.funding, True, SearchMode.FUZZY)
        )

    person_queries.append(_search_by_opt_out_es_query(False))

    should_clauses = []
    if company_queries:
        should_clauses.append(
            Q("nested", path="companies", query=Q("bool", must=company_queries))
        )
    if request.mode == SearchMode.FUZZY:
        if company_fuzzy_queries:
            should_clauses.append(
                Q(
                    "nested",
                    path="companies_fuzzy",
                    query=Q("bool", must=company_fuzzy_queries),
                )
            )
    if should_clauses:
        person_queries.append(Q("bool", should=should_clauses))
    search_es_query = Q("bool", must=person_queries)
    return search_es_query
