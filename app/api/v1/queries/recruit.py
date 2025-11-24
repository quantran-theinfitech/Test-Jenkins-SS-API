# flake8: noqa: E501

from datetime import datetime, timedelta
from typing import List

from elasticsearch_dsl import Q
from sqlalchemy import text
from sqlmodel import Session

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
    _search_by_exclude_corporate_numbers_es_query,
    _search_by_framework_technologies_es_query,
    _search_by_funding_es_query,
    _search_by_industries_es_query,
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
)
from app.api.v1.schemas.search_cross import SearchCrossRequest, SearchMode
from app.api.v1.schemas.search_recruits import (
    ApplicationFlow,
    EmploymentType,
    FeatureFlag,
    Holiday,
    Keyword,
    KeywordSearch,
    Location,
    MediaCode,
    PostingPeriod,
    RecruitQualification,
    Salary,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.collections.get_corporate_number_by_collection_ids import (
    get_corporate_numbers_by_collection_ids,
)
from app.api.v1.services.enrichments import get_entity_identifier_by_enrichment_id
from utils.extract_domain import (
    normalized_domain_search_companies,
    normalized_sns_url_search_persons,
    split_string_by_newline,
)


def build_es_query(
    request: SearchCrossRequest,
    db: Session,
    current_user: UserBase,
):

    request = normalized_sns_url_search_persons(
        normalized_domain_search_companies(request)
    )
    recruit_queries = []
    recruit_queries.append(_filter_by_start_at_es_query(False))
    recruit_queries.extend([Q("exists", field="updated_at")])
    company_queries = []
    if request.recruit:
        recruit = request.recruit
        if recruit.keyword:
            recruit_queries.append(
                _search_by_recruit_keyword_es_query(recruit.keyword, False)
            )
        if recruit.media:
            recruit_queries.append(
                _search_by_publication_media_es_query(recruit.media, False)
            )
        if recruit.employment_type:
            recruit_queries.append(
                _search_by_employment_type_es_query(recruit.employment_type, False)
            )
        if recruit.feature_flag:
            recruit_queries.append(
                _search_by_feature_flag_es_query(recruit.feature_flag, False)
            )
        if recruit.salary_year:
            recruit_queries.append(
                _search_by_salary_es_query(recruit.salary_year, False, "YEAR")
            )
        if recruit.salary_month:
            recruit_queries.append(
                _search_by_salary_es_query(recruit.salary_month, False, "MONTH")
            )
        if recruit.job_skill_codes:
            recruit_queries.append(
                _search_by_job_skill_codes_es_query(recruit.job_skill_codes, False)
            )

        if recruit.posting_period:
            recruit_queries.append(
                _search_by_recruit_at_es_query(recruit.posting_period, False)
            )
        if recruit.locations:
            recruit_queries.append(
                _search_by_recruit_locations_es_query(recruit.locations, False)
            )
        if recruit.address:
            recruit_queries.append(_search_by_address_es_query(recruit.address, False))
        if recruit.application_flow:
            recruit_queries.append(
                _search_by_application_flow_es_query(recruit.application_flow, False)
            )
        if recruit.job_category:
            category_queries = []
            category = recruit.job_category
            if category.large_category:
                for large_category in category.large_category:
                    category_queries.append(
                        _search_by_job_categories_es_query(large_category, False)
                    )
            if category.sub_category:
                for sub_category in category.sub_category:
                    category_queries.append(
                        _search_by_job_sub_categories_es_query(sub_category.sub, False)
                    )
            recruit_queries.append(Q("bool", should=category_queries))
        if recruit.tech_frameworks:
            recruit_queries.append(
                _search_by_tech_frameworks_es_query(recruit.tech_frameworks, False)
            )
        if recruit.tech_languages:
            recruit_queries.append(
                _search_by_tech_languages_es_query(recruit.tech_languages, False)
            )
        if recruit.holiday:
            recruit_queries.append(_search_by_holiday_es_query(recruit.holiday, False))
        if recruit.recruit_qualifications:
            recruit_queries.append(
                _search_by_recruit_qualifications_es_query(
                    recruit.recruit_qualifications, False
                )
            )
    if request.company_keywords:
        if request.company_keywords.is_exact:
            company_queries.extend(
                _search_by_exact_company_keyword_es_query(
                    request.company_keywords, True, SearchMode.EXACT
                )
            )
        else:
            company_queries.extend(
                _search_by_company_keyword_es_query(
                    request.company_keywords, True, SearchMode.EXACT
                )
            )
    if request.industries:
        company_queries.append(
            _search_by_industries_es_query(request.industries, True, SearchMode.EXACT)
        )
    if request.locations:
        company_queries.append(
            _search_by_locations_es_query(request.locations, True, SearchMode.EXACT)
        )
    if request.company_name:
        company_queries.extend(
            _search_by_company_name_es_query(
                split_string_by_newline(request.company_name),
                True,
                SearchMode.EXACT,
            )
        )
    if request.domain_name:
        company_queries.extend(
            _search_by_domain_name_es_query(request.domain_name, True, SearchMode.EXACT)
        )

    if request.date_of_establishment:
        company_queries.extend(
            _search_by_establish_at_es_query(
                request.date_of_establishment, True, SearchMode.EXACT
            )
        )

    if request.closing_month:
        company_queries.extend(
            _search_by_closing_month_es_query(
                request.closing_month, True, SearchMode.EXACT
            )
        )

    if request.listing_division:
        company_queries.extend(
            _search_by_listing_division_es_query(
                request.listing_division, True, SearchMode.EXACT
            )
        )
    if request.listed_exchanges:
        company_queries.append(
            _search_by_listed_exchanges_es_query(
                request.listed_exchanges, True, SearchMode.EXACT
            )
        )
    if request.average_age:
        company_queries.extend(
            _search_by_average_age_es_query(request.average_age, True, SearchMode.EXACT)
        )

    if request.marketing_tools:
        company_queries.extend(
            _search_by_marketing_tools_es_query(
                request.marketing_tools, True, SearchMode.EXACT
            )
        )

    if request.communication_tools:
        company_queries.extend(
            _search_by_communication_tools_es_query(
                request.communication_tools, True, SearchMode.EXACT
            )
        )

    if request.management_tools:
        company_queries.extend(
            _search_by_management_tools_es_query(
                request.management_tools, True, SearchMode.EXACT
            )
        )

    if request.other_tools:
        company_queries.extend(
            _search_by_other_tools_es_query(request.other_tools, True, SearchMode.EXACT)
        )

    if request.language_technologies:
        company_queries.extend(
            _search_by_language_technologies_es_query(
                request.language_technologies, True, SearchMode.EXACT
            )
        )

    if request.framework_technologies:
        company_queries.extend(
            _search_by_framework_technologies_es_query(
                request.framework_technologies, True, SearchMode.EXACT
            )
        )

    if request.cloud_services:
        company_queries.extend(
            _search_by_cloud_services_es_query(
                request.cloud_services, True, SearchMode.EXACT
            )
        )

    if request.number_of_employees:
        company_queries.extend(
            _search_by_number_of_employees_es_query(
                request.number_of_employees, True, SearchMode.EXACT
            )
        )

    if request.capital:
        company_queries.extend(
            _search_by_capital_es_query(request.capital, True, SearchMode.EXACT)
        )

    if request.revenue:
        company_queries.append(
            _search_by_revenue_es_query(request.revenue, True, SearchMode.EXACT)
        )
    if request.contact_information:
        company_queries.append(
            _search_by_contact_information_es_query(
                request.contact_information, True, SearchMode.EXACT
            )
        )

    if request.business_models:
        company_queries.extend(
            _search_by_business_model_codes_es_query(
                request.business_models, True, SearchMode.EXACT
            )
        )

    if request.tags:
        tag_query = """
                SELECT tc.corporate_number
                FROM team_companies tc
                WHERE tc.team_id = :team_id
                    AND tags && :tags
                """
        corporate_numbers_by_tags = [
            row[0]
            for row in db.execute(
                text(tag_query),
                {
                    "team_id": current_user.team_id,
                    "tags": "{{{}}}".format(
                        ", ".join(f'"{item}"' for item in set(request.tags))
                    ),
                },
            ).all()
        ]
        company_queries.append(
            _search_by_corporate_numbers_es_query(
                corporate_numbers_by_tags, True, SearchMode.EXACT
            )
        )

    if request.corporate_numbers:
        recruit_queries.append(
            _search_by_corporate_numbers_es_query(
                request.corporate_numbers,
                False,
                SearchMode.EXACT,
            )
        )

    if request.exclude_corporate_numbers:
        recruit_queries.append(
            _search_by_exclude_corporate_numbers_es_query(
                request.exclude_corporate_numbers, False, SearchMode.EXACT
            )
        )

    if request.original_tags:
        company_queries.append(
            _search_by_original_tags_es_query(
                request.original_tags, True, SearchMode.EXACT
            )
        )
    if request.funding:
        company_queries.append(
            _search_by_funding_es_query(request.funding, True, SearchMode.EXACT)
        )
    if request.is_companies_unlocked:
        companies_downloaded_query = """
            SELECT tc.corporate_number
            FROM team_companies tc
            LEFT JOIN companies c ON tc.corporate_number = c.corporate_number
            WHERE tc.team_id = :team_id"""

        corporate_numbers_downloaded = [
            row[0]
            for row in db.execute(
                text(companies_downloaded_query),
                {
                    "team_id": current_user.team_id,
                },
            ).all()
        ]
        if len(corporate_numbers_downloaded) >= 0:
            company_queries.append(
                _search_by_corporate_numbers_es_query(
                    corporate_numbers_downloaded, False, SearchMode.EXACT
                )
            )
    if request.company_collections:
        corporate_numbers_by_collection = get_corporate_numbers_by_collection_ids(
            db, request.company_collections, current_user
        )
        recruit_queries.extend(
            _search_by_company_collections_es_query(
                corporate_numbers_by_collection,
                request.company_collections,
                False,
                SearchMode.EXACT,
            )
        )
    if request.companies_identified:
        corporate_numbers_identified = get_entity_identifier_by_enrichment_id(
            db, current_user, request.companies_identified.enrichment_ids
        )
        recruit_queries.extend(
            _search_by_company_identified_es_query(
                corporate_numbers_identified,
                False,
                SearchMode.EXACT,
            )
        )
    if company_queries:
        recruit_queries.extend(company_queries)
    return Q("bool", must=recruit_queries)


def _search_by_recruit_keyword_es_query(keyword: Keyword, idx_company: bool):
    queries = []
    fields = ["title", "content", "tags", "search_keywords"]
    if idx_company:
        fields = [f"recruits__{field}" for field in fields]

    def build_keyword_query(
        list_keyword: List[str], field: str, is_exact: bool = keyword.is_exact
    ):
        return [
            Q("match_phrase", **{field: kw}) if is_exact else Q("match", **{field: kw})
            for kw in list_keyword
        ]

    if keyword.and_keywords:
        field_queries = [
            build_keyword_query(keyword.and_keywords, field) for field in fields
        ]
        queries.append(
            Q(
                "bool",
                should=[Q("bool", must=field_query) for field_query in field_queries],
            )
        )
    if keyword.or_keywords:
        field_queries = [
            build_keyword_query(keyword.or_keywords, field) for field in fields
        ]
        queries.append(
            Q(
                "bool",
                should=[Q("bool", should=field_query) for field_query in field_queries],
            )
        )
    if keyword.exclude_keywords:
        field_queries = [
            build_keyword_query(keyword.exclude_keywords, field) for field in fields
        ]
        queries.append(
            Q(
                "bool",
                must_not=[
                    Q("bool", should=field_query) for field_query in field_queries
                ],
            )
        )
    return Q("bool", must=queries)


def _search_by_keyword_es_query(keyword: Keyword, idx_company: bool):
    queries = []
    if keyword.and_keywords:
        title_query = (
            [
                (
                    (Q("match_phrase", recruits__title=kw))
                    if keyword.is_exact
                    else (Q("match", recruits__title=kw))
                )
                for kw in keyword.and_keywords
            ]
            if idx_company
            else [
                (
                    (Q("match_phrase", title=kw))
                    if keyword.is_exact
                    else (Q("match", title=kw))
                )
                for kw in keyword.and_keywords
            ]
        )
        content_query = (
            [
                (
                    (Q("match_phrase", recruits__content=kw))
                    if keyword.is_exact
                    else (Q("match", recruits__content=kw))
                )
                for kw in keyword.and_keywords
            ]
            if idx_company
            else [
                (
                    (Q("match_phrase", content=kw))
                    if keyword.is_exact
                    else (Q("match", content=kw))
                )
                for kw in keyword.and_keywords
            ]
        )
        queries.append(
            Q(
                "bool",
                should=[Q("bool", must=title_query), Q("bool", must=content_query)],
            )
        )
    if keyword.or_keywords:
        title_query = (
            [
                (
                    (Q("match_phrase", recruits__title=kw))
                    if keyword.is_exact
                    else (Q("match", recruits__title=kw))
                )
                for kw in keyword.or_keywords
            ]
            if idx_company
            else [
                (
                    (Q("match_phrase", title=kw))
                    if keyword.is_exact
                    else (Q("match", title=kw))
                )
                for kw in keyword.or_keywords
            ]
        )
        content_query = (
            [
                (
                    (Q("match_phrase", recruits__content=kw))
                    if keyword.is_exact
                    else (Q("match", recruits__content=kw))
                )
                for kw in keyword.or_keywords
            ]
            if idx_company
            else [
                (
                    (Q("match_phrase", content=kw))
                    if keyword.is_exact
                    else (Q("match", content=kw))
                )
                for kw in keyword.or_keywords
            ]
        )
        queries.append(
            Q(
                "bool",
                should=[Q("bool", should=title_query), Q("bool", should=content_query)],
            )
        )
    if keyword.exclude_keywords:
        title_query = (
            [
                (
                    (Q("match_phrase", recruits__title=kw))
                    if keyword.is_exact
                    else (Q("match", recruits__title=kw))
                )
                for kw in keyword.exclude_keywords
            ]
            if idx_company
            else [
                (
                    (Q("match_phrase", title=kw))
                    if keyword.is_exact
                    else (Q("match", title=kw))
                )
                for kw in keyword.exclude_keywords
            ]
        )
        content_query = (
            [
                (
                    (Q("match_phrase", recruits__content=kw))
                    if keyword.is_exact
                    else (Q("match", recruits__content=kw))
                )
                for kw in keyword.exclude_keywords
            ]
            if idx_company
            else [
                (
                    (Q("match_phrase", content=kw))
                    if keyword.is_exact
                    else (Q("match", content=kw))
                )
                for kw in keyword.exclude_keywords
            ]
        )
        queries.append(
            Q(
                "bool",
                must_not=[
                    Q("bool", should=title_query),
                    Q("bool", should=content_query),
                ],
            )
        )
    return Q("bool", must=queries)


def _search_by_publication_media_es_query(
    publication_media: List[MediaCode], idx_company: bool
):
    return (
        Q("terms", recruits__media_code=publication_media)
        if idx_company
        else Q("terms", media_code=publication_media)
    )


def _search_by_employment_type_es_query(
    employment_type: List[EmploymentType], idx_company: bool
):
    return (
        Q("terms", recruits__employment_type_codes=employment_type)
        if idx_company
        else Q("terms", employment_type_codes=employment_type)
    )


def _search_by_feature_flag_es_query(
    feature_flag: List[FeatureFlag], idx_company: bool
):
    queries = []
    for feature in feature_flag:
        if feature == FeatureFlag.EDUCATIONAL:
            queries.append(
                Q("term", **{f"recruits__required_educational_flag": True})
                if idx_company
                else Q("term", **{"required_educational_flag": True})
            )
        elif feature == FeatureFlag.COLLEGE:
            queries.append(
                Q("term", **{f"recruits__required_college_flag": True})
                if idx_company
                else Q("term", **{"required_college_flag": True})
            )
        elif feature == FeatureFlag.UNIVERSITY_GRADUATION:
            queries.append(
                Q("term", **{f"recruits__required_university_graduate_flag": True})
                if idx_company
                else Q("term", **{"required_university_graduate_flag": True})
            )
        elif feature == FeatureFlag.POST_GRADUATE:
            queries.append(
                Q("term", **{f"recruits__required_post_graduate_flag": True})
                if idx_company
                else Q("term", **{"required_post_graduate_flag": True})
            )
    return Q("bool", should=queries)


def _search_by_salary_es_query(salary: Salary, idx_company: bool, type: str):
    queries = []
    if type == "MONTH":
        "recruits.salary_month_min" if idx_company else "salary_month_min"
        "recruits.salary_month_max" if idx_company else "salary_month_max"
        salary_value = (
            "recruits.salary_month_value" if idx_company else "salary_month_value"
        )
    elif type == "YEAR":
        "recruits.salary_year_min" if idx_company else "salary_year_min"
        "recruits.salary_year_max" if idx_company else "salary_year_max"
        salary_value = (
            "recruits.salary_year_value" if idx_company else "salary_year_value"
        )
    if salary.exclude_unknown_flag:
        queries.append(Q("exists", field=salary_value))
    if salary.gte:
        queries.append(Q("range", **{salary_value: {"gte": salary.gte}}))
    if salary.lte:
        queries.append(Q("range", **{salary_value: {"lte": salary.lte}}))
    return Q("bool", must=queries)


def _search_by_recruit_at_es_query(recruit_at: List[PostingPeriod], idx_company: bool):
    posting_period_ranges = {
        PostingPeriod.ONE_MONTH: (timedelta(days=30), timedelta(days=0)),
        PostingPeriod.ONE_TO_THREE_MONTH: (timedelta(days=90), timedelta(days=30)),
        PostingPeriod.THREE_TO_SIX_MONTH: (timedelta(days=180), timedelta(days=90)),
        PostingPeriod.SIX_TO_ONE_YEAR: (timedelta(days=365), timedelta(days=180)),
    }
    now = datetime.now()
    posting_period_queries = []
    for period in recruit_at:
        if period in posting_period_ranges:
            delta_start, delta_end = posting_period_ranges[period]
            start_at = now - delta_start
            end_at = now - delta_end
            posting_period_queries.append(
                Q(
                    "range",
                    recruits__start_at={"gte": start_at, "lte": end_at},
                )
                if idx_company
                else Q("range", start_at={"gte": start_at, "lte": end_at})
            )
        elif period == PostingPeriod.ONE_YEAR_OR_MORE:
            end_at = now - timedelta(days=365)
            posting_period_queries.append(
                Q("range", recruits__start_at={"lte": end_at})
                if idx_company
                else Q("range", start_at={"lte": end_at})
            )
    return Q("bool", should=posting_period_queries)


def _search_by_recruit_locations_es_query(locations: Location, idx_company: bool):
    queries = []
    if locations.prefectures:
        queries.append(
            Q("terms", nta_prefecture_id=locations.prefectures)
            if idx_company
            else Q("terms", prefecture_codes=locations.prefectures)
        )
    if locations.cities:
        queries.append(
            Q("terms", nta_city_id=locations.cities)
            if idx_company
            else Q("terms", city_codes=locations.cities)
        )
    return Q("bool", should=queries)


def _search_by_application_flow_es_query(
    application_flow: List[ApplicationFlow], idx_company: bool
):
    return (
        Q("terms", recruits__application_flow_codes=application_flow)
        if idx_company
        else Q("terms", application_flow_codes=application_flow)
    )


def _search_by_job_positions_es_query(job_positions: str, idx_company: bool):
    return (
        Q("match", recruits__positions=job_positions)
        if idx_company
        else Q("match", job_positions=job_positions)
    )


def _search_by_job_categories_es_query(job_categories: str, idx_company: bool):
    return (
        Q("term", recruits__category_codes=job_categories)
        if idx_company
        else Q("term", category_codes=job_categories)
    )


def _search_by_job_sub_categories_es_query(job_sub_categories: str, idx_company: bool):
    return (
        Q("term", recruits__sub_category_codes=job_sub_categories)
        if idx_company
        else Q("term", sub_category_codes=job_sub_categories)
    )


def _search_by_job_skill_codes_es_query(
    job_skill_codes: KeywordSearch, idx_company: bool
):
    or_queries = []
    exclude_queries = []
    if job_skill_codes.or_keywords:
        or_queries.append(
            Q("terms", recruits__job_skill_codes=job_skill_codes.or_keywords)
            if idx_company
            else Q("terms", job_skill_codes=job_skill_codes.or_keywords)
        )
    if job_skill_codes.exclude_keywords:
        exclude_queries.append(
            Q(
                "terms",
                recruits__job_skill_codes=job_skill_codes.exclude_keywords,
            )
            if idx_company
            else Q("terms", job_skill_codes=job_skill_codes.exclude_keywords)
        )
    return Q("bool", should=or_queries, must_not=exclude_queries)


def _search_by_address_es_query(address: str, idx_company: bool):
    return (
        Q("match", recruits__working_address_list=address)
        if idx_company
        else Q("match", working_address_list=address)
    )


def _search_by_tech_frameworks_es_query(
    tech_frameworks: KeywordSearch, idx_company: bool
):
    or_queries = []
    exclude_queries = []
    if tech_frameworks.or_keywords:
        or_queries.append(
            Q(
                "terms",
                recruits__job_tech_frameworks=tech_frameworks.or_keywords,
            )
            if idx_company
            else Q("terms", job_tech_frameworks=tech_frameworks.or_keywords)
        )
    if tech_frameworks.exclude_keywords:
        exclude_queries.append(
            Q(
                "terms",
                recruits__job_tech_frameworks=tech_frameworks.exclude_keywords,
            )
            if idx_company
            else Q("terms", job_tech_frameworks=tech_frameworks.exclude_keywords)
        )
    return Q("bool", should=or_queries, must_not=exclude_queries)


def _search_by_tech_languages_es_query(
    tech_languages: KeywordSearch, idx_company: bool
):
    or_queries = []
    exclude_queries = []
    if tech_languages.or_keywords:
        or_queries.append(
            Q("terms", recruits__job_tech_languages=tech_languages.or_keywords)
            if idx_company
            else Q("terms", job_tech_languages=tech_languages.or_keywords)
        )
    if tech_languages.exclude_keywords:
        exclude_queries.append(
            Q(
                "terms",
                recruits__job_tech_languages=tech_languages.exclude_keywords,
            )
            if idx_company
            else Q("terms", job_tech_languages=tech_languages.exclude_keywords)
        )
    return Q("bool", should=or_queries, must_not=exclude_queries)


def _search_by_holiday_es_query(holiday: Holiday, idx_company: bool):
    queries = []

    if holiday.holiday_codes:
        queries.append(
            Q("terms", recruits__holiday_codes=holiday.holiday_codes)
            if idx_company
            else Q("terms", holiday_codes=holiday.holiday_codes)
        )
    if holiday.holiday_year:
        if holiday.holiday_year.gte:
            queries.append(
                Q("range", recruits__holiday_year_min={"gte": holiday.holiday_year.gte})
                if idx_company
                else Q("range", holiday_year_min={"gte": holiday.holiday_year.gte})
            )
        if holiday.holiday_year.lte:
            queries.append(
                Q("range", recruits__holiday_year_min={"lte": holiday.holiday_year.lte})
                if idx_company
                else Q("range", holiday_year_min={"lte": holiday.holiday_year.lte})
            )
    return Q("bool", must=queries)


def _search_by_recruit_qualifications_es_query(
    recruit_qualifications: KeywordSearch, idx_company: bool
):
    or_queries = []
    exclude_queries = []
    if recruit_qualifications.or_keywords:
        or_queries.append(
            Q(
                "terms",
                recruits__recruit_qualifications=recruit_qualifications.or_keywords,
            )
            if idx_company
            else Q(
                "terms",
                job_recruit_qualifications=recruit_qualifications.or_keywords,
            )
        )
    if recruit_qualifications.exclude_keywords:
        exclude_queries.append(
            Q(
                "terms",
                recruits__recruit_qualifications=recruit_qualifications.exclude_keywords,
            )
            if idx_company
            else Q(
                "terms",
                job_recruit_qualifications=recruit_qualifications.exclude_keywords,
            )
        )
    return Q("bool", should=or_queries, must_not=exclude_queries)


def _filter_by_start_at_es_query(idx_company: bool = False):
    if idx_company:
        return Q(
            "range", recruits__start_at={"gte": datetime.now() - timedelta(days=180)}
        )
    else:
        return Q("range", start_at={"gte": datetime.now() - timedelta(days=180)})
