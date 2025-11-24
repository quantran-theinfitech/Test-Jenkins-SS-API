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
    _search_by_revenue_es_query,
    _search_by_role_code_es_query,
    _search_by_role_code_groups_es_query,
    _search_by_sns_urls_es_query,
    _search_by_uuid_es_query,
    build_press_release_es_query,
)
from app.api.v1.queries.recruit import (
    _filter_by_start_at_es_query,
    _search_by_address_es_query,
    _search_by_application_flow_es_query,
    _search_by_employment_type_es_query,
    _search_by_feature_flag_es_query,
    _search_by_holiday_es_query,
    _search_by_job_categories_es_query,
    _search_by_job_skill_codes_es_query,
    _search_by_job_sub_categories_es_query,
    _search_by_publication_media_es_query,
    _search_by_recruit_at_es_query,
    _search_by_recruit_keyword_es_query,
    _search_by_recruit_locations_es_query,
    _search_by_recruit_qualifications_es_query,
    _search_by_salary_es_query,
    _search_by_tech_frameworks_es_query,
    _search_by_tech_languages_es_query,
)
from app.api.v1.schemas.search_cross import SearchCrossRequest, SearchMode
from utils.extract_domain import split_string_by_newline
from utils.optimize_name import optimize_name, translate_roles


def build_es_query(
    search_condition: SearchCrossRequest,
    corporate_numbers_by_tags: List[str] = [],
    corporate_numbers_downloaded: List[str] = [],
    corporate_numbers_csv: List[str] = [],
    persons_uuids: List[str] = [],
    press_release_business_categories: List[str] = [],
    is_unlimited_account: bool = False,
):
    company_queries = []
    person_queries = []
    if search_condition.company_keywords:
        if search_condition.company_keywords.is_exact:
            company_queries.extend(
                _search_by_exact_company_keyword_es_query(
                    search=search_condition.company_keywords,
                    is_nested=False,
                    mode=SearchMode.EXACT,
                )
            )
        else:
            company_queries.extend(
                _search_by_company_keyword_es_query(
                    search=search_condition.company_keywords,
                    is_nested=False,
                    mode=SearchMode.EXACT,
                )
            )

    if search_condition.person_keywords:
        if search_condition.person_keywords.is_exact:
            person_queries.extend(
                _search_by_exact_person_keyword_es_query(
                    search_condition.person_keywords, True
                )
            )
        else:
            person_queries.extend(
                _search_by_person_keyword_es_query(
                    search_condition.person_keywords, True
                )
            )

    if search_condition.keyword:
        company_queries.append(
            _search_by_keyword_es_query(
                optimize_name(search_condition.keyword), False, SearchMode.EXACT
            )
        )

    if search_condition.industries:
        company_queries.append(
            _search_by_industries_es_query(
                search_condition.industries, False, SearchMode.EXACT
            )
        )

    if search_condition.locations:
        company_queries.append(
            _search_by_locations_es_query(
                search_condition.locations, False, SearchMode.EXACT
            )
        )

    if search_condition.company_name:
        company_queries.extend(
            _search_by_company_name_es_query(
                split_string_by_newline(search_condition.company_name),
                False,
                SearchMode.EXACT,
            )
        )

    if search_condition.domain_name:
        company_queries.extend(
            _search_by_domain_name_es_query(
                search_condition.domain_name, False, SearchMode.EXACT
            )
        )

    if search_condition.date_of_establishment:
        company_queries.extend(
            _search_by_establish_at_es_query(
                search_condition.date_of_establishment, False, SearchMode.EXACT
            )
        )

    if search_condition.closing_month:
        company_queries.extend(
            _search_by_closing_month_es_query(
                search_condition.closing_month, False, SearchMode.EXACT
            )
        )

    if search_condition.listing_division:
        company_queries.extend(
            _search_by_listing_division_es_query(
                search_condition.listing_division, False, SearchMode.EXACT
            )
        )

    if search_condition.listed_exchanges:
        company_queries.append(
            _search_by_listed_exchanges_es_query(
                search_condition.listed_exchanges, False, SearchMode.EXACT
            )
        )

    if search_condition.average_age:
        company_queries.extend(
            _search_by_average_age_es_query(
                search_condition.average_age, False, SearchMode.EXACT
            )
        )

    if search_condition.marketing_tools:
        company_queries.extend(
            _search_by_marketing_tools_es_query(
                search_condition.marketing_tools, False, SearchMode.EXACT
            )
        )

    if search_condition.communication_tools:
        company_queries.extend(
            _search_by_communication_tools_es_query(
                search_condition.communication_tools, False, SearchMode.EXACT
            )
        )

    if search_condition.management_tools:
        company_queries.extend(
            _search_by_management_tools_es_query(
                search_condition.management_tools, False, SearchMode.EXACT
            )
        )

    if search_condition.other_tools:
        company_queries.extend(
            _search_by_other_tools_es_query(
                search_condition.other_tools, False, SearchMode.EXACT
            )
        )

    if search_condition.language_technologies:
        company_queries.extend(
            _search_by_language_technologies_es_query(
                search_condition.language_technologies, False, SearchMode.EXACT
            )
        )

    if search_condition.framework_technologies:
        company_queries.extend(
            _search_by_framework_technologies_es_query(
                search_condition.framework_technologies, False, SearchMode.EXACT
            )
        )

    if search_condition.cloud_services:
        company_queries.extend(
            _search_by_cloud_services_es_query(
                search_condition.cloud_services, False, SearchMode.EXACT
            )
        )

    if search_condition.number_of_employees:
        company_queries.extend(
            _search_by_number_of_employees_es_query(
                search_condition.number_of_employees, False, SearchMode.EXACT
            )
        )

    if search_condition.capital:
        company_queries.extend(
            _search_by_capital_es_query(
                search_condition.capital, False, SearchMode.EXACT
            )
        )

    if search_condition.revenue:
        company_queries.append(
            _search_by_revenue_es_query(
                search_condition.revenue, False, SearchMode.EXACT
            )
        )

    if search_condition.job_update_date:
        company_queries.append(
            _search_by_job_update_date_es_query(
                search_condition.job_update_date, False, SearchMode.EXACT
            )
        )

    if search_condition.contact_information:
        company_queries.append(
            _search_by_contact_information_es_query(
                search_condition.contact_information, False, SearchMode.EXACT
            )
        )

    if search_condition.business_models:
        company_queries.extend(
            _search_by_business_model_codes_es_query(
                search_condition.business_models, False, SearchMode.EXACT
            )
        )

    if search_condition.tags:
        company_queries.append(
            _search_by_corporate_numbers_es_query(
                corporate_numbers_by_tags, False, SearchMode.EXACT
            )
        )

    if search_condition.corporate_numbers:
        company_queries.append(
            _search_by_corporate_numbers_es_query(
                search_condition.corporate_numbers,
                False,
                SearchMode.EXACT,
            )
        )

    if search_condition.exclude_corporate_numbers:
        company_queries.append(
            _search_by_exclude_corporate_numbers_es_query(
                search_condition.exclude_corporate_numbers,
                False,
                SearchMode.EXACT,
            )
        )

    if search_condition.original_tags:
        company_queries.append(
            _search_by_original_tags_es_query(
                search_condition.original_tags, False, SearchMode.EXACT
            )
        )

    if search_condition.name:
        name_queries = _search_by_name_es_query(
            split_string_by_newline(search_condition.name), True
        )
        person_queries.append(Q("bool", should=name_queries, minimum_should_match=1))

    if search_condition.role_codes:
        person_queries.append(
            _search_by_role_code_es_query(search_condition.role_codes, True)
        )
    if search_condition.role_group_codes:
        person_queries.append(
            _search_by_role_code_groups_es_query(
                translate_roles(search_condition.role_group_codes), True
            )
        )
    if search_condition.sns_url:
        person_queries.append(
            _search_by_sns_urls_es_query(
                split_string_by_newline(search_condition.sns_url), True
            )
        )

    if search_condition.platform:
        person_queries.append(
            _search_by_platform_es_query(search_condition.platform, True)
        )

    if search_condition.is_companies_unlocked and not is_unlimited_account:
        if len(corporate_numbers_downloaded) >= 0:
            company_queries.append(
                _search_by_corporate_numbers_es_query(
                    corporate_numbers_downloaded, False, SearchMode.EXACT
                )
            )

    if search_condition.is_persons_unlocked:
        if len(persons_uuids) >= 0:
            person_queries.append(_search_by_uuid_es_query(persons_uuids, True))

    if len(corporate_numbers_csv) > 0:
        company_queries.append(
            _search_by_corporate_numbers_es_query(
                corporate_numbers_csv, False, SearchMode.EXACT
            )
        )

    if search_condition.corporate_numbers_by_collection:
        company_queries.extend(
            _search_by_company_collections_es_query(
                search_condition.corporate_numbers_by_collection,
                search_condition.company_collections,
                False,
                SearchMode.EXACT,
            )
        )
    if search_condition.corporate_numbers_identified:
        company_queries.extend(
            _search_by_company_identified_es_query(
                search_condition.corporate_numbers_identified,
                False,
                SearchMode.EXACT,
            )
        )
    if search_condition.uuids_by_collection:
        person_queries.extend(
            _search_by_person_collections_es_query(
                search_condition.uuids_by_collection,
                search_condition.person_collections,
                True,
            )
        )

    if search_condition.funding:
        company_queries.append(
            _search_by_funding_es_query(
                search_condition.funding, False, SearchMode.EXACT
            )
        )
    if search_condition.recruit:
        recruit = search_condition.recruit
        recruit_queries = []
        recruit_queries.append(_filter_by_start_at_es_query(True))
        if recruit.keyword:
            recruit_queries.append(
                _search_by_recruit_keyword_es_query(recruit.keyword, True)
            )
        if recruit.media:
            recruit_queries.append(
                _search_by_publication_media_es_query(recruit.media, True)
            )
        if recruit.employment_type:
            recruit_queries.append(
                _search_by_employment_type_es_query(recruit.employment_type, True)
            )
        if recruit.feature_flag:
            recruit_queries.append(
                _search_by_feature_flag_es_query(recruit.feature_flag, True)
            )
        if recruit.salary_year:
            recruit_queries.append(
                _search_by_salary_es_query(recruit.salary_year, True, "YEAR")
            )
        if recruit.salary_month:
            recruit_queries.append(
                _search_by_salary_es_query(recruit.salary_month, True, "MONTH")
            )
        if recruit.posting_period:
            recruit_queries.append(
                _search_by_recruit_at_es_query(recruit.posting_period, True)
            )
        if recruit.locations:
            company_queries.append(
                _search_by_recruit_locations_es_query(recruit.locations, True)
            )
        if recruit.application_flow:
            recruit_queries.append(
                _search_by_application_flow_es_query(recruit.application_flow, True)
            )
        if recruit.job_category:
            category_queries = []
            category = recruit.job_category
            if category.large_category:
                for large_category in category.large_category:
                    category_queries.append(
                        _search_by_job_categories_es_query(large_category, True)
                    )
            if category.sub_category:
                for sub_category in category.sub_category:
                    category_queries.append(
                        _search_by_job_sub_categories_es_query(sub_category.sub, True)
                    )
            recruit_queries.append(Q("bool", should=category_queries))
        if recruit.job_skill_codes:
            recruit_queries.append(
                _search_by_job_skill_codes_es_query(recruit.job_skill_codes, True)
            )
        if recruit.address:
            recruit_queries.append(_search_by_address_es_query(recruit.address, True))
        if recruit.tech_frameworks:
            recruit_queries.append(
                _search_by_tech_frameworks_es_query(recruit.tech_frameworks, True)
            )
        if recruit.tech_languages:
            recruit_queries.append(
                _search_by_tech_languages_es_query(recruit.tech_languages, True)
            )
        if recruit.holiday:
            recruit_queries.append(_search_by_holiday_es_query(recruit.holiday, True))
        if recruit.recruit_qualifications:
            recruit_queries.append(
                _search_by_recruit_qualifications_es_query(
                    recruit.recruit_qualifications, True
                )
            )
        if len(recruit_queries) > 0:
            company_queries.append(
                Q("nested", path="recruits", query=Q("bool", must=recruit_queries))
            )
    if search_condition.new_press_release:
        press_release_query = build_press_release_es_query(
            search_condition.new_press_release, True, press_release_business_categories
        )
        if len(press_release_query) > 0:
            company_queries.append(
                Q(
                    "nested",
                    path="press_releases",
                    query=Q("bool", must=press_release_query),
                )
            )

    company_queries.append(_search_by_opt_out_es_query(True))
    if person_queries:
        company_queries.append(
            Q("nested", path="persons", query=Q("bool", must=person_queries))
        )
    search_es_query = Q(
        "bool",
        must=company_queries,
    )
    return search_es_query
