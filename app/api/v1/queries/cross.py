# flake8: noqa: E501
from datetime import datetime, timedelta
from typing import List

from elasticsearch_dsl import Q

from app.api.v1.schemas.companies import FilterWappalyzer
from app.api.v1.schemas.search_cross import (
    BusinessModel,
    Capital,
    ClosingMonth,
    CollectionList,
    CompanyIndustry,
    ContactInformation,
    CorporateNumberByCollection,
    CorporateNumberByIdentified,
    DurationFunding,
    EstablishAt,
    Funding,
    JobUpdateDate,
    Keyword,
    KeywordSearch,
    ListingDivision,
    Location,
    NumberRangeWithFlag,
    NumberRangeWithoutFlag,
    Platform,
    PostingPeriod,
    PressRelease,
    Revenue,
    SearchMode,
    SearchPersonRequest,
    UuidsByCollection,
)
from app.api.v1.schemas.search_press_releases import (
    PostingPeriod,
    SearchPressReleaseRequest,
)
from app.constant.constants import (
    CLOUD_SERVICES_COMMON,
    COMMUNICATION_TOOLS_COMMON,
    FRAMEWORK_TECHNOLOGIES_COMMON,
    INDUSTRIES_CATEGORIES,
    LANGUAGE_TECHNOLOGIES_COMMON,
    MANAGEMENT_TOOLS_COMMON,
    MARKETING_TOOLS_COMMON,
    OTHER_TOOLS_WAPPALYZER,
)
from utils.extract_domain import split_string_by_newline
from utils.optimize_name import optimize_name, translate_roles

# TODO: Need add function search cross for:
# industry_keywords, location_keywords, business_content, factories_count,
# listing_year, average_salary, average_work_duration, publication_media,
# job_category, employment_type, occupation_codes, occupation_keywords,
# job_skill_codes, job_skill_code_keywords, job_locations, job_location_keywords,
# job_keywords, job_salary, job_salary_keywords, job_annual_income


def filter_wappalyzer_keywords(
    exclude_keywords: List[str], or_keywords: List[str], type: FilterWappalyzer
):
    if type == FilterWappalyzer.MANAGEMENT_TOOLS:
        tools_dict = MANAGEMENT_TOOLS_COMMON
    elif type == FilterWappalyzer.COMMUNICATION_TOOLS:
        tools_dict = COMMUNICATION_TOOLS_COMMON
    elif type == FilterWappalyzer.LANGUAGE_TECHNOLOGIES:
        tools_dict = LANGUAGE_TECHNOLOGIES_COMMON
    elif type == FilterWappalyzer.FRAMEWORK_TECHNOLOGIES:
        tools_dict = FRAMEWORK_TECHNOLOGIES_COMMON
    elif type == FilterWappalyzer.CLOUD_SERVICES:
        tools_dict = CLOUD_SERVICES_COMMON
    elif type == FilterWappalyzer.MARKETING_TOOLS:
        tools_dict = MARKETING_TOOLS_COMMON

    tools_set = set(tools_dict.keys())

    exclude_keywords_wappalyzer = [
        tools_dict[keyword]
        for keyword in (exclude_keywords or [])
        if keyword in tools_set
    ]

    or_keywords_wappalyzer = [
        tools_dict[keyword] for keyword in (or_keywords or []) if keyword in tools_set
    ]

    return exclude_keywords_wappalyzer, or_keywords_wappalyzer


def _search_by_exact_company_keyword_es_query(
    search: Keyword, is_nested: bool, mode: SearchMode
):
    queries = []

    # Define fields with their boost values
    fields = [
        "name^2.0",
        "kana_name^2.0",
        "english_name^2.0",
        "business_content^1.0",
        "landing_html_content^1.0",
        "info_html_content^1.0",
        "business_html_content^1.0",
    ]

    def create_multi_match_query(
        keyword: str, optimize_keyword: bool = False, path: str = None
    ):
        query_text = optimize_name(keyword) if optimize_keyword else keyword
        query_fields = [f"{path}.{field}" for field in fields] if is_nested else fields
        return Q(
            "multi_match",
            query=query_text,
            fields=query_fields,
            type="phrase",  # For exact matching
            slop=0,  # No words allowed between terms
            lenient=True,  # Handle field type mismatches
        )

    if search.and_keywords:
        if mode == SearchMode.EXACT:
            and_queries = [
                create_multi_match_query(
                    keyword, optimize_keyword=True, path="companies"
                )
                for keyword in search.and_keywords
            ]
        else:
            and_queries = [
                create_multi_match_query(
                    keyword, optimize_keyword=True, path="companies_fuzzy"
                )
                for keyword in search.and_keywords
            ]
        queries.append(
            Q("bool", must=and_queries)
        )  # All queries must match (AND condition)

    if search.or_keywords:
        if mode == SearchMode.EXACT:
            or_queries = [
                create_multi_match_query(
                    keyword, optimize_keyword=True, path="companies"
                )
                for keyword in search.or_keywords
            ]
        else:
            or_queries = [
                create_multi_match_query(
                    keyword, optimize_keyword=True, path="companies_fuzzy"
                )
                for keyword in search.or_keywords
            ]
        queries.append(
            Q(
                "bool",
                should=or_queries,  # At least one query should match (OR condition)
                minimum_should_match=1,
            )
        )

    if search.exclude_keywords:
        if mode == SearchMode.EXACT:
            exclude_queries = [
                create_multi_match_query(
                    keyword, optimize_keyword=True, path="companies"
                )
                for keyword in search.exclude_keywords
            ]
        else:
            exclude_queries = [
                create_multi_match_query(
                    keyword, optimize_keyword=True, path="companies_fuzzy"
                )
                for keyword in search.exclude_keywords
            ]
        queries.append(
            Q(
                "bool",
                must_not=exclude_queries,  # None of these queries should match (NOT condition)
            )
        )

    return queries


def _search_by_company_keyword_es_query(
    search: Keyword, is_nested: bool, mode: SearchMode
):
    queries = []
    fields = [
        "name^2.0",
        "kana_name^2.0",
        "english_name^2.0",
        "business_content^1.0",
        "landing_html_content^1.0",
        "info_html_content^1.0",
        "business_html_content^1.0",
    ]

    def create_multi_match_query(keyword: str, optimize_keyword: bool, path: str):
        query_text = optimize_name(keyword) if optimize_keyword else keyword
        query_fields = [f"{path}.{field}" for field in fields] if is_nested else fields
        return Q(
            "multi_match",
            query=query_text,
            fields=query_fields,
            lenient=True,  # Handle field type mismatches
        )

    if search.and_keywords:
        if mode == SearchMode.EXACT:
            and_queries = [
                create_multi_match_query(
                    keyword, optimize_keyword=True, path="companies"
                )
                for keyword in search.and_keywords
            ]
        else:
            and_queries = [
                create_multi_match_query(
                    keyword, optimize_keyword=True, path="companies_fuzzy"
                )
                for keyword in search.and_keywords
            ]
        queries.append(
            Q("bool", must=and_queries)
        )  # All queries must match (AND condition)
    if search.or_keywords:
        if mode == SearchMode.EXACT:
            or_queries = [
                create_multi_match_query(
                    keyword, optimize_keyword=True, path="companies"
                )
                for keyword in search.or_keywords
            ]
        else:
            or_queries = [
                create_multi_match_query(
                    keyword, optimize_keyword=True, path="companies_fuzzy"
                )
                for keyword in search.or_keywords
            ]
        queries.append(
            Q(
                "bool",
                should=or_queries,  # At least one query should match (OR condition)
                minimum_should_match=1,
            )
        )
    if search.exclude_keywords:
        if mode == SearchMode.EXACT:
            exclude_queries = [
                create_multi_match_query(
                    keyword, optimize_keyword=True, path="companies"
                )
                for keyword in search.exclude_keywords
            ]
        else:
            exclude_queries = [
                create_multi_match_query(
                    keyword, optimize_keyword=True, path="companies_fuzzy"
                )
                for keyword in search.exclude_keywords
            ]
        queries.append(
            Q(
                "bool",
                must_not=exclude_queries,  # None of these queries should match (NOT condition)
            )
        )

    return queries


def _search_by_exact_person_keyword_es_query(search: Keyword, is_nested: bool):
    queries = []
    fields = ["intro^2.0", "role_name^2.0", "bio^1.0", "name^2.0"]

    def create_multi_match_query(keyword: str, path: str = None):
        query_fields = [f"{path}.{field}" for field in fields] if is_nested else fields
        return Q(
            "multi_match",
            query=keyword,
            fields=query_fields,
            type="phrase",  # For exact matching
            slop=0,  # No words allowed between terms
            lenient=True,  # Handle field type mismatches
        )

    if search.and_keywords:
        and_queries = [
            create_multi_match_query(keyword, path="persons")
            for keyword in search.and_keywords
        ]
        queries.append(Q("bool", must=and_queries))

    if search.or_keywords:
        or_queries = [
            create_multi_match_query(keyword, path="persons")
            for keyword in search.or_keywords
        ]
        queries.append(
            Q(
                "bool",
                should=or_queries,  # At least one query should match (OR condition)
                minimum_should_match=1,
            )
        )

    if search.exclude_keywords:
        exclude_queries = [
            create_multi_match_query(keyword, path="persons")
            for keyword in search.exclude_keywords
        ]
        queries.append(
            Q(
                "bool",
                must_not=exclude_queries,  # None of these queries should match (NOT condition)
            )
        )

    return queries


def _search_by_person_keyword_es_query(search: Keyword, is_nested: bool):
    queries = []
    fields = ["intro^2.0", "role_name^2.0", "bio^1.0", "name^2.0"]

    def create_multi_match_query(keyword: str, path: str):
        query_fields = [f"{path}.{field}" for field in fields] if is_nested else fields
        return Q(
            "multi_match",
            query=keyword,
            fields=query_fields,
            lenient=True,  # Handle field type mismatches
        )

    if search.and_keywords:
        and_queries = [
            create_multi_match_query(keyword, path="persons")
            for keyword in search.and_keywords
        ]
        queries.append(Q("bool", must=and_queries))
    if search.or_keywords:
        or_queries = [
            create_multi_match_query(keyword, path="persons")
            for keyword in search.or_keywords
        ]
        queries.append(
            Q(
                "bool",
                should=or_queries,  # At least one query should match (OR condition)
                minimum_should_match=1,
            )
        )
    if search.exclude_keywords:
        exclude_queries = [
            create_multi_match_query(keyword, path="persons")
            for keyword in search.exclude_keywords
        ]
        queries.append(
            Q(
                "bool",
                must_not=exclude_queries,  # None of these queries should match (NOT condition)
            )
        )
    return queries


def _search_by_keyword_es_query(keyword: str, is_nested: bool, mode: SearchMode):
    fields = [
        "name^1.2",
        "kana_name^1",
        "english_name^1",
        "business_content^0.8",
    ]
    query = Q(
        "multi_match",
        query=keyword,
        fields=fields,
        type="best_fields",
    )
    if is_nested:
        path = "companies"
        query._setattr("fields", [f"{path}.{field}" for field in fields])
        if mode == SearchMode.FUZZY:
            fuzzy_path = "companies_fuzzy"
            fuzzy_query = Q(
                "multi_match",
                query=keyword,
                fields=[f"{fuzzy_path}.{field}" for field in fields],
                type="best_fields",
            )
            return fuzzy_query
        else:
            return query
    else:
        return query


def _search_by_industries_es_query(
    industries: CompanyIndustry, is_nested: bool, mode: SearchMode
):
    if industries.large_industries:
        sub_industries_list = []
        for large_industry in industries.large_industries:
            sub_industries_list.extend(
                x["code"]
                for x in INDUSTRIES_CATEGORIES.get(large_industry, {}).get("child", [])
            )
        if industries.sub_industries:
            industries.sub_industries.extend(sub_industries_list)
        else:
            industries.sub_industries = sub_industries_list
    queries = []
    if is_nested:
        if industries.sub_industries:
            queries.append(
                Q("terms", companies__sub_industries_code=industries.sub_industries)
                if mode != SearchMode.FUZZY
                else Q(
                    "terms",
                    companies_fuzzy__sub_industries_code=industries.sub_industries,
                )
            )

        return Q("bool", should=queries)
    else:
        if industries.sub_industries:
            queries.append(Q("terms", sub_industries_code=industries.sub_industries))
        return Q("bool", should=queries)


def _search_by_locations_es_query(
    locations: Location, is_nested: bool, mode: SearchMode
):
    queries = []
    if is_nested:
        if locations.prefectures:
            queries.append(
                Q("terms", companies_fuzzy__nta_prefecture_id=locations.prefectures)
                if mode == SearchMode.FUZZY
                else Q("terms", companies__nta_prefecture_id=locations.prefectures)
            )

        if locations.cities:
            queries.append(
                Q("terms", companies__nta_city_id=locations.cities)
                if mode != SearchMode.FUZZY
                else Q("terms", companies_fuzzy__nta_city_id=locations.cities)
            )
        return Q("bool", should=queries)
    else:
        if locations.prefectures:
            queries.append(Q("terms", nta_prefecture_id=locations.prefectures))
        if locations.cities:
            queries.append(Q("terms", nta_city_id=locations.cities))
        return Q("bool", should=queries)


def _search_by_company_name_es_query(
    company_name: List[str], is_nested: bool, mode: SearchMode
):
    queries = []
    fields = ["name", "kana_name", "english_name"]
    if is_nested:
        fields = (
            [f"companies.{field}" for field in fields]
            if mode != SearchMode.FUZZY
            else [f"companies_fuzzy.{field}" for field in fields]
        )
    field_and_queries = []
    for field in fields:
        should_queries = [
            Q("match", **{field: optimize_name(keyword)}) for keyword in company_name
        ]
        for keyword in company_name:
            should_queries.append(Q("match", **{field: optimize_name(keyword)}))
            should_queries.append(
                Q("match", **{field: optimize_name(keyword).replace(" ", "")})
            )
        field_and_queries.append(Q("bool", should=should_queries))

    queries.append(Q("bool", should=field_and_queries, minimum_should_match=1))
    return queries


def _search_by_domain_name_es_query(
    domain_name: List[str], is_nested: bool, mode: SearchMode
):
    queries = []
    if is_nested:
        queries.append(
            Q("terms", companies__domain=domain_name)
            if mode != SearchMode.FUZZY
            else Q("terms", companies_fuzzy__domain=domain_name)
        )
    else:
        queries.append(Q("terms", domain=domain_name))

    return queries


def _search_by_establish_at_es_query(
    establish_at: EstablishAt, is_nested: bool, mode: SearchMode
):
    queries = []

    if is_nested:
        field = "companies.establish_at"
        prefix = "companies__establish_at"
        if mode == SearchMode.FUZZY:
            field = "companies_fuzzy.establish_at"
            prefix = "companies_fuzzy__establish_at"
    else:
        field = "establish_at"
        prefix = "establish_at"

    if establish_at.exclude_unknown_flag:
        exists_query = Q("exists", field=field)
        queries.append(exists_query)
    range_blocks = []
    range_conditions = []

    if establish_at.start_date is not None:
        range_conditions.append(
            Q("range", **{prefix: {"gte": establish_at.start_date}})
        )

    if establish_at.end_date is not None:
        range_conditions.append(Q("range", **{prefix: {"lte": establish_at.end_date}}))

    if range_conditions:
        range_blocks.append(Q("bool", must=range_conditions))
    if range_blocks:
        queries.append(Q("bool", should=range_blocks, minimum_should_match=1))

    return queries


def _search_by_closing_month_es_query(
    closing_month: ClosingMonth, is_nested: bool, mode: SearchMode
):
    queries = []

    if is_nested:
        field = "companies.closing_month"
        prefix = "companies__closing_month"
        if mode == SearchMode.FUZZY:
            field = "companies_fuzzy.closing_month"
            prefix = "companies_fuzzy__closing_month"
    else:
        field = "closing_month"
        prefix = "closing_month"

    if closing_month.exclude_unknown_flag:
        queries.append(Q("exists", field=field))

    if closing_month.months:
        queries.append(Q("terms", **{prefix: closing_month.months}))
    return queries


def _search_by_listing_division_es_query(
    listing_division: ListingDivision, is_nested: bool, mode: SearchMode
):
    queries = []
    queries_listing_division = []
    if is_nested:
        if mode == SearchMode.FUZZY:
            field = "companies_fuzzy.listing_market_code"
        else:
            field = "companies.listing_market_code"
    else:
        field = "listing_market_code"

    if listing_division.exclude_unknown_flag:
        queries.append(Q("exists", field=field))
    if listing_division.listed:
        query = Q(
            "bool",
            must=Q("exists", field=field),
            must_not=Q("match", **{field: "UNLISTED"}),
        )
        queries_listing_division.append(query)

    if listing_division.unlisted:
        queries_listing_division.append(Q("match", **{field: "UNLISTED"}))

    if len(queries_listing_division) > 0:
        query = Q("bool", should=queries_listing_division)
        queries.append(query)

    return queries


def _search_by_listed_exchanges_es_query(
    listed_exchanges: List[str], is_nested: bool, mode: SearchMode
):
    if is_nested:
        query = Q("terms", companies__listing_market_code=listed_exchanges)
        if mode == SearchMode.FUZZY:
            return Q("terms", companies_fuzzy__listing_market_code=listed_exchanges)
        else:
            return query
    else:
        return Q("terms", listing_market_code=listed_exchanges)


def _build_range_query(field_name, age_range):
    range_query = {}
    if age_range.gte is not None:
        range_query["gte"] = age_range.gte
    if age_range.lte is not None:
        range_query["lte"] = age_range.lte
    return {"range": {field_name: range_query}}


def create_range_query(field_name, gte=None, lte=None):
    range_filter = {}
    if gte is not None:
        range_filter["gte"] = gte
    if lte is not None:
        range_filter["lte"] = lte
    return Q("range", **{field_name: range_filter})


def _search_by_average_age_es_query(
    average_age: List[NumberRangeWithoutFlag], is_nested: bool, mode: SearchMode
):
    if not average_age:
        return []
    field_name = "companies__average_age" if is_nested else "average_age"
    bool_query = []

    for age_range in average_age:
        range_query = create_range_query(field_name, age_range.gte, age_range.lte)
        if is_nested:
            if mode == SearchMode.FUZZY:
                bool_query = [
                    create_range_query(
                        "companies_fuzzy__average_age", age_range.gte, age_range.lte
                    )
                ]
            else:
                bool_query.append(range_query)
        else:
            bool_query.append(range_query)

    return [Q("bool", should=bool_query)] if bool_query else []


def _search_by_press_release_es_query(
    keyword: KeywordSearch, is_nested: bool, mode: SearchMode
):
    queries = []
    if keyword.exclude_keywords:
        if is_nested:
            exclude_query = Q(
                "nested",
                path="companies",
                query=Q(
                    "bool",
                    must_not=Q(
                        "terms",
                        companies__press_release_media_codes=keyword.exclude_keywords,
                    ),
                ),
            )
        else:
            exclude_query = Q(
                "bool",
                must_not=Q("terms", press_release_media_codes=keyword.exclude_keywords),
            )
        queries.append(exclude_query)

    if keyword.or_keywords:
        if is_nested:
            or_query = Q(
                "nested",
                path="companies",
                query=Q(
                    "terms",
                    companies__press_release_media_codes=keyword.or_keywords,
                ),
            )
            if mode == SearchMode.FUZZY:
                fuzzy_or_query = Q(
                    "nested",
                    path="companies_fuzzy",
                    query=Q(
                        "terms",
                        companies_fuzzy__press_release_media_codes=keyword.or_keywords,
                    ),
                )
                queries.append(
                    Q(
                        "nested",
                        path="companies_fuzzy",
                        query=Q("bool", should=fuzzy_or_query),
                    )
                )
        else:
            or_query = Q("terms", press_release_media_codes=keyword.or_keywords)
        queries.append(or_query)
    return queries


def _search_by_new_press_release_es_query(press_release: PressRelease):
    from datetime import datetime, timedelta

    queries = []
    if press_release.posting_period:
        posting_period_ranges = {
            PostingPeriod.ONE_MONTH: (timedelta(days=30), timedelta(days=0)),
            PostingPeriod.ONE_TO_THREE_MONTH: (timedelta(days=90), timedelta(days=30)),
            PostingPeriod.THREE_TO_SIX_MONTH: (timedelta(days=180), timedelta(days=90)),
            PostingPeriod.SIX_TO_ONE_YEAR: (timedelta(days=365), timedelta(days=180)),
        }
        now = datetime.now()

        if press_release.posting_period:
            posting_period_queries = []
            for period in press_release.posting_period:
                if period in posting_period_ranges:
                    delta_start, delta_end = posting_period_ranges[period]
                    start_at = now - delta_start
                    end_at = now - delta_end
                    posting_period_queries.append(
                        Q(
                            "nested",
                            path="press_releases",
                            query=Q(
                                "range",
                                press_releases__posted_at={
                                    "gte": start_at,
                                    "lte": end_at,
                                },
                            ),
                        )
                    )
                elif period == PostingPeriod.ONE_YEAR_OR_MORE:
                    end_at = now - timedelta(days=365)
                    posting_period_queries.append(
                        Q(
                            "nested",
                            path="press_releases",
                            query=Q("range", press_releases__posted_at={"lte": end_at}),
                        )
                    )
            queries.append(Q("bool", should=posting_period_queries))
    if press_release.media:
        media_queries = []
        for media in press_release.media:
            media_queries.append(
                Q(
                    "nested",
                    path="press_releases",
                    query=Q("match", press_releases__media_code=media.value),
                )
            )
        queries.append(Q("bool", should=media_queries))
    if press_release.keyword:
        search = press_release.keyword
        if search.and_keywords:
            title_query = [
                (
                    (Q("match_phrase", press_releases__title=keyword))
                    if search.is_exact
                    else (Q("match", press_releases__title=keyword))
                )
                for keyword in search.and_keywords
            ]
            content_query = [
                (
                    (Q("match_phrase", press_releases__content=keyword))
                    if search.is_exact
                    else (Q("match", press_releases__content=keyword))
                )
                for keyword in search.and_keywords
            ]
            keyword_queries = Q(
                "bool",
                should=[Q("bool", must=title_query), Q("bool", must=content_query)],
            )
            queries.append(Q("nested", path="press_releases", query=keyword_queries))

        if search.or_keywords:
            title_query = [
                (
                    (Q("match_phrase", press_releases__title=keyword))
                    if search.is_exact
                    else (Q("match", press_releases__title=keyword))
                )
                for keyword in search.or_keywords
            ]
            content_query = [
                (
                    (Q("match_phrase", press_releases__content=keyword))
                    if search.is_exact
                    else (Q("match", press_releases__content=keyword))
                )
                for keyword in search.or_keywords
            ]
            keyword_queries = Q(
                "bool",
                should=[Q("bool", should=title_query), Q("bool", should=content_query)],
            )
            queries.append(Q("nested", path="press_releases", query=keyword_queries))

        if search.exclude_keywords:
            exclude_nested_queries = []
            for keyword in search.exclude_keywords:
                match_title = (
                    Q("match_phrase", press_releases__title=keyword)
                    if search.is_exact
                    else Q("match", press_releases__title=keyword)
                )
                match_content = (
                    Q("match_phrase", press_releases__content=keyword)
                    if search.is_exact
                    else Q("match", press_releases__content=keyword)
                )
                exclude_nested_queries.append(
                    Q("nested", path="press_releases", query=match_title)
                )
                exclude_nested_queries.append(
                    Q("nested", path="press_releases", query=match_content)
                )
            queries.append(Q("bool", must_not=exclude_nested_queries))

    return Q("bool", must=queries)


def _search_by_tools(
    tools: KeywordSearch, is_nested: bool, type: FilterWappalyzer, mode: SearchMode
):
    exclude_keywords_wappalyzer, or_keywords_wappalyzer = filter_wappalyzer_keywords(
        tools.exclude_keywords,
        tools.or_keywords,
        type,
    )

    return _search_by_tools_func(
        tools.exclude_keywords,
        tools.or_keywords,
        is_nested,
        type,
        exclude_keywords_wappalyzer,
        or_keywords_wappalyzer,
        mode,
    )


def _search_by_tools_func(
    exclude_keywords: List[str],
    or_keywords: List[str],
    is_nested: bool,
    type: FilterWappalyzer,
    exclude_keywords_wappalyzer: List[str],
    or_keywords_wappalyzer: List[str],
    mode: SearchMode,
):
    queries = []

    tool_type = f"{type.value}"
    companies_type = f"companies__{type.value}"
    if mode == SearchMode.FUZZY:
        companies_type = f"companies_fuzzy__{type.value}"

    must_query = []

    if is_nested:
        if exclude_keywords:
            must_query.append(
                Q(
                    "terms",
                    **{companies_type: exclude_keywords},
                )
            )

        if exclude_keywords_wappalyzer:
            must_query.append(
                Q(
                    "terms",
                    companies__technologies__name=exclude_keywords_wappalyzer,
                )
            )
    else:
        if exclude_keywords:
            must_query.append(Q("terms", **{tool_type: exclude_keywords}))

        if exclude_keywords_wappalyzer:
            must_query.append(
                Q(
                    "terms",
                    companies__technologies__name=exclude_keywords_wappalyzer,
                )
            )

    queries.append(Q("bool", must_not=must_query))

    should_queries = []

    if is_nested:
        if or_keywords:
            should_queries.append(
                Q(
                    "terms",
                    **{companies_type: or_keywords},
                ),
            )

        if or_keywords_wappalyzer:
            should_queries.append(
                Q(
                    "terms",
                    companies__technologies__name=or_keywords_wappalyzer,
                )
            )
        if mode == SearchMode.FUZZY:
            if or_keywords:
                should_queries = [
                    Q(
                        "terms",
                        **{companies_type: or_keywords},
                    )
                ]
                should_queries.append(
                    Q(
                        "terms",
                        companies_fuzzy__technologies__name=or_keywords_wappalyzer,
                    )
                )

    else:
        if or_keywords:
            should_queries.append(Q("terms", **{tool_type: or_keywords}))

        if or_keywords_wappalyzer:
            should_queries.append(Q("terms", technologies__name=or_keywords_wappalyzer))

    queries.append(Q("bool", should=should_queries, minimum_should_match=1))

    return queries


def _search_by_marketing_tools_es_query(
    marketing_tools: KeywordSearch, is_nested: bool, mode: SearchMode
):
    return _search_by_tools(
        marketing_tools, is_nested, FilterWappalyzer.MARKETING_TOOLS, mode
    )


def _search_by_communication_tools_es_query(
    keywords: KeywordSearch, is_nested: bool, mode: SearchMode
):
    return _search_by_tools(
        keywords, is_nested, FilterWappalyzer.COMMUNICATION_TOOLS, mode
    )


def _search_by_management_tools_es_query(
    management_tools: KeywordSearch, is_nested: bool, mode: SearchMode
):
    return _search_by_tools(
        management_tools, is_nested, FilterWappalyzer.MANAGEMENT_TOOLS, mode
    )


def _search_by_language_technologies_es_query(
    keywords: KeywordSearch, is_nested: bool, mode: SearchMode
):
    return _search_by_tools(
        keywords, is_nested, FilterWappalyzer.LANGUAGE_TECHNOLOGIES, mode
    )


def _search_by_framework_technologies_es_query(
    keywords: KeywordSearch, is_nested: bool, mode: SearchMode
):
    return _search_by_tools(
        keywords, is_nested, FilterWappalyzer.FRAMEWORK_TECHNOLOGIES, mode
    )


def _search_by_cloud_services_es_query(
    cloud_services: KeywordSearch, is_nested: bool, mode: SearchMode
):
    return _search_by_tools(
        cloud_services, is_nested, FilterWappalyzer.CLOUD_SERVICES, mode
    )


def _search_by_other_tools_es_query(
    other_tools: KeywordSearch, is_nested: bool, mode: SearchMode
):
    other_tools_dict = OTHER_TOOLS_WAPPALYZER
    other_tools_set = set(OTHER_TOOLS_WAPPALYZER.keys())

    exclude_keywords = [
        keyword
        for keyword in (other_tools.exclude_keywords or [])
        if keyword not in other_tools_set
    ]

    or_keywords = [
        keyword
        for keyword in (other_tools.or_keywords or [])
        if keyword not in other_tools_set
    ]

    exclude_keywords_wappalyzer = [
        other_tools_dict[keyword]
        for keyword in (other_tools.exclude_keywords or [])
        if keyword in other_tools_set
    ]

    or_keywords_wappalyzer = [
        other_tools_dict[keyword]
        for keyword in (other_tools.or_keywords or [])
        if keyword in other_tools_set
    ]

    return _search_by_tools_func(
        exclude_keywords,
        or_keywords,
        is_nested,
        FilterWappalyzer.OTHER_TOOLS,
        exclude_keywords_wappalyzer,
        or_keywords_wappalyzer,
        mode,
    )


def _search_by_exclude_corporate_numbers_es_query(
    corporate_numbers: List[str], is_nested: bool, mode: SearchMode
):
    if is_nested:
        if mode == SearchMode.FUZZY:
            return Q(
                "bool",
                must_not=Q(
                    "terms", companies_fuzzy__corporate_number=corporate_numbers
                ),
            )
        else:
            return Q(
                "bool",
                must_not=Q("terms", companies__corporate_number=corporate_numbers),
            )
    else:
        return Q("bool", must_not=Q("terms", corporate_number=corporate_numbers))


def _search_by_corporate_numbers_es_query(
    corporate_numbers: List[str], is_nested: bool, mode: SearchMode
):
    if is_nested:
        if mode == SearchMode.FUZZY:
            return Q("terms", companies_fuzzy__corporate_number=corporate_numbers)
        else:
            return Q("terms", companies__corporate_number=corporate_numbers)
    else:
        return Q("terms", corporate_number=corporate_numbers)


def _search_by_original_tags_es_query(
    original_tags: List[str], is_nested: bool, mode: SearchMode
):
    if is_nested:
        query = Q(
            "terms",
            companies__original_tags=original_tags,
        )
        if mode == SearchMode.FUZZY:
            return Q(
                "terms",
                companies_fuzzy__original_tags=original_tags,
            )
        else:
            return query
    else:
        return Q(
            "terms",
            original_tags=original_tags,
        )


def _search_by_number_of_employees_es_query(
    number_of_employees: NumberRangeWithFlag, is_nested: bool, mode: SearchMode
):
    queries = []

    if is_nested:
        field = "companies.employees_count"
        prefix = "companies__employees_count"
        if mode == SearchMode.FUZZY:
            field = "companies_fuzzy.employees_count"
            prefix = "companies_fuzzy__employees_count"
    else:
        field = "employees_count"
        prefix = "employees_count"

    if number_of_employees.exclude_unknown_flag:
        exists_query = Q("exists", field=field)
        queries.append(exists_query)

    if number_of_employees.ranges:
        range_blocks = []

        for range_item in number_of_employees.ranges:
            range_conditions = []

            if range_item.gte is not None:
                range_conditions.append(Q("range", **{prefix: {"gte": range_item.gte}}))

            if range_item.lte is not None:
                range_conditions.append(Q("range", **{prefix: {"lte": range_item.lte}}))

            if range_conditions:
                range_block = Q("bool", must=range_conditions)
                range_blocks.append(range_block)

        if range_blocks:
            queries.append(Q("bool", should=range_blocks, minimum_should_match=1))
    return queries


def _search_by_capital_es_query(capital: Capital, is_nested: bool, mode: SearchMode):
    queries = []

    if is_nested:
        field = "companies.capital"
        prefix = "companies__capital"
        if mode == SearchMode.FUZZY:
            field = "companies_fuzzy.capital"
            prefix = "companies_fuzzy__capital"
    else:
        field = "capital"
        prefix = "capital"

    if capital.exclude_unknown_flag:
        exists_query = Q("exists", field=field)
        queries.append(exists_query)

    if capital.ranges:
        range_blocks = []

        for range_item in capital.ranges:
            range_conditions = []

            if range_item.gte is not None:
                range_conditions.append(Q("range", **{prefix: {"gte": range_item.gte}}))

            if range_item.lte is not None:
                range_conditions.append(Q("range", **{prefix: {"lte": range_item.lte}}))

            if range_conditions:
                range_block = Q("bool", must=range_conditions)
                range_blocks.append(range_block)

        if range_blocks:
            queries.append(Q("bool", should=range_blocks, minimum_should_match=1))

    return queries


def _search_by_revenue_es_query(revenue: Revenue, is_nested: bool, mode: SearchMode):
    query_revenue = []
    if is_nested:
        field = "companies.revenue"
        prefix = "companies__revenue"
        if mode == SearchMode.FUZZY:
            field = "companies_fuzzy.revenue"
            prefix = "companies_fuzzy__revenue"
    else:
        field = "revenue"
        prefix = "revenue"

    if revenue.exclude_unknown_flag:
        exists_query = Q("exists", field=field)
        query_revenue.append(exists_query)

    if revenue.ranges:
        range_blocks = []

        for range_item in revenue.ranges:
            range_conditions = []

            if range_item.gte is not None:
                range_conditions.append(Q("range", **{prefix: {"gte": range_item.gte}}))

            if range_item.lte is not None:
                range_conditions.append(Q("range", **{prefix: {"lte": range_item.lte}}))

            if range_conditions:
                range_block = Q("bool", must=range_conditions)
                range_blocks.append(range_block)

        if range_blocks:
            query_revenue.append(Q("bool", should=range_blocks, minimum_should_match=1))
    query_revenue_ai = []
    if is_nested:
        field = "companies.revenue_ai"
        prefix = "companies__revenue_ai"
        if mode == SearchMode.FUZZY:
            field = "companies_fuzzy.revenue_ai"
            prefix = "companies_fuzzy__revenue_ai"
    else:
        field = "revenue_ai"
        prefix = "revenue_ai"

    if revenue.exclude_unknown_flag:
        exists_query = Q("exists", field=field)
        query_revenue_ai.append(exists_query)
    if revenue.ranges:
        range_blocks = []

        for range_item in revenue.ranges:
            range_conditions = []

            if range_item.gte is not None:
                range_conditions.append(Q("range", **{prefix: {"gte": range_item.gte}}))

            if range_item.lte is not None:
                range_conditions.append(Q("range", **{prefix: {"lte": range_item.lte}}))

            if range_conditions:
                range_block = Q("bool", must=range_conditions)
                range_blocks.append(range_block)

        if range_blocks:
            query_revenue_ai.append(
                Q("bool", should=range_blocks, minimum_should_match=1)
            )
    return Q(
        "bool", should=[Q("bool", must=query_revenue), Q("bool", must=query_revenue_ai)]
    )


def _search_by_job_update_date_es_query(
    job_update_date: JobUpdateDate, is_nested: bool, mode: SearchMode
):
    queries = []
    if job_update_date.halfway:
        if job_update_date.halfway.start_date:
            if is_nested:
                gte_es_query = Q(
                    "range",
                    companies__latest_recruits_at={
                        "gte": job_update_date.halfway.start_date
                    },
                )
                queries.append(gte_es_query)
                if mode == SearchMode.FUZZY:
                    fuzzy_gte_es_query = Q(
                        "range",
                        companies_fuzzy__latest_recruits_at={
                            "gte": job_update_date.halfway.start_date
                        },
                    )
                    queries.append(fuzzy_gte_es_query)
            else:
                gte_es_query = Q(
                    "range",
                    latest_recruits_at={"gte": job_update_date.halfway.start_date},
                )
                queries.append(gte_es_query)
        if job_update_date.halfway.end_date:
            if is_nested:
                lte_es_query = Q(
                    "range",
                    companies__latest_recruits_at={
                        "lte": job_update_date.halfway.end_date
                    },
                )
                queries.append(lte_es_query)
                if mode == SearchMode.FUZZY:
                    fuzzy_lte_es_query = Q(
                        "range",
                        companies_fuzzy__latest_recruits_at={
                            "lte": job_update_date.halfway.end_date
                        },
                    )
                    queries.append(fuzzy_lte_es_query)
            else:
                lte_es_query = Q(
                    "range",
                    latest_recruits_at={"lte": job_update_date.halfway.end_date},
                )
                queries.append(lte_es_query)

    if job_update_date.new_graduate:
        if job_update_date.new_graduate.start_date:
            if is_nested:
                gte_es_query = Q(
                    "range",
                    companies__latest_new_graduate_recruit_at={
                        "gte": job_update_date.new_graduate.start_date
                    },
                )
                queries.append(gte_es_query)
                if mode == SearchMode.FUZZY:
                    fuzzy_gte_es_query = Q(
                        "range",
                        companies_fuzzy__latest_new_graduate_recruit_at={
                            "gte": job_update_date.new_graduate.start_date
                        },
                    )
                    queries.append(fuzzy_gte_es_query)
            else:
                gte_es_query = Q(
                    "range",
                    latest_new_graduate_recruit_at={
                        "gte": job_update_date.new_graduate.start_date
                    },
                )
                queries.append(gte_es_query)
        if job_update_date.new_graduate.end_date:
            if is_nested:
                lte_es_query = Q(
                    "range",
                    companies__latest_new_graduate_recruit_at={
                        "lte": job_update_date.new_graduate.end_date
                    },
                )
                queries.append(lte_es_query)
                if mode == SearchMode.FUZZY:
                    fuzzy_lte_es_query = Q(
                        "range",
                        companies_fuzzy__latest_new_graduate_recruit_at={
                            "lte": job_update_date.new_graduate.end_date
                        },
                    )
                    queries.append(fuzzy_lte_es_query)
            else:
                lte_es_query = Q(
                    "range",
                    latest_new_graduate_recruit_at={
                        "lte": job_update_date.new_graduate.end_date
                    },
                )
                queries.append(lte_es_query)

    if job_update_date.part_time:
        if job_update_date.part_time.start_date:
            if is_nested:
                gte_es_query = Q(
                    "range",
                    companies__latest_parttime_recruit_at={
                        "gte": job_update_date.part_time.start_date
                    },
                )
                queries.append(gte_es_query)
                if mode == SearchMode.FUZZY:
                    fuzzy_gte_es_query = Q(
                        "range",
                        companies_fuzzy__latest_parttime_recruit_at={
                            "gte": job_update_date.part_time.start_date
                        },
                    )
                    queries.append(fuzzy_gte_es_query)
            else:
                gte_es_query = Q(
                    "range",
                    latest_parttime_recruit_at={
                        "gte": job_update_date.part_time.start_date
                    },
                )
                queries.append(gte_es_query)
        if job_update_date.part_time.end_date:
            if is_nested:
                lte_es_query = Q(
                    "range",
                    companies__latest_parttime_recruit_at={
                        "lte": job_update_date.part_time.end_date
                    },
                )
                queries.append(lte_es_query)
                if mode == SearchMode.FUZZY:
                    fuzzy_lte_es_query = Q(
                        "range",
                        companies_fuzzy__latest_parttime_recruit_at={
                            "lte": job_update_date.part_time.end_date
                        },
                    )
                    queries.append(fuzzy_lte_es_query)
            else:
                lte_es_query = Q(
                    "range",
                    latest_parttime_recruit_at={
                        "lte": job_update_date.part_time.end_date
                    },
                )
                queries.append(lte_es_query)

    if is_nested:
        return Q("nested", path="companies", query=Q("bool", must=queries))
    else:
        return Q("bool", must=queries)


def _add_exists_query(
    contact: str, is_nested: bool, queries: List, path_prefix: str = ""
):
    """Helper function to add 'exists' query to the list."""
    queries.append(
        Q("exists", field=f"{path_prefix}{contact}" if is_nested else contact)
    )


def _handle_sns_company(is_nested: bool, queries: List, mode: SearchMode):
    """Handle the sns_company logic separately for both nested and non-nested."""
    sns_queries = [
        Q("exists", field="twitter_url"),
        Q("exists", field="facebook_url"),
    ]
    if is_nested:
        if mode == SearchMode.FUZZY:
            sns_queries = [
                Q("exists", field="companies_fuzzy.twitter_url"),
                Q("exists", field="companies_fuzzy.facebook_url"),
            ]
        else:
            sns_queries = [
                Q("exists", field="companies.twitter_url"),
                Q("exists", field="companies.facebook_url"),
            ]
    queries.append(Q("bool", should=sns_queries))


def _handle_contact(contact, is_nested, queries, mode: SearchMode):
    if contact == "sns_company":
        _handle_sns_company(is_nested, queries, mode)
    else:
        if is_nested:
            if mode == SearchMode.FUZZY:
                path_prefix = "companies_fuzzy."
            else:
                path_prefix = "companies."
        else:
            path_prefix = ""
        _add_exists_query(contact, is_nested, queries, path_prefix)


def _search_by_contact_information_es_query(
    contact_information: ContactInformation, is_nested: bool, mode: SearchMode
):
    fields = [
        "contact_form_url",
        "recruit_phone",
        "phone",
        "fax",
        "recruit_email",
        "contact_email",
        "hp_url",
        "sns_company",
    ]
    queries = []

    if contact_information.contact_info:
        for contact in contact_information.contact_info:
            if contact in fields:
                _handle_contact(contact, is_nested, queries, mode)

    query_type = (
        Q("bool", must=queries)
        if contact_information.operator == "AND"
        else Q("bool", should=queries)
    )
    return query_type


def _search_by_business_model_codes_es_query(
    business_models: BusinessModel, is_nested: bool, mode: SearchMode
):
    queries = []

    if is_nested:
        field = "companies.business_model_codes"
        prefix = "companies__business_model_codes"
        if mode == SearchMode.FUZZY:
            field = "companies_fuzzy.business_model_codes"
            prefix = "companies_fuzzy__business_model_codes"
    else:
        field = "business_model_codes"
        prefix = "business_model_codes"

    if business_models.exclude_unknown_flag:
        queries.append(Q("exists", field=field))

    if business_models.business_model_codes:
        queries.append(Q("terms", **{prefix: business_models.business_model_codes}))

    return queries


def _search_by_name_es_query(person_names: List[str], is_nested: bool):
    queries = []
    for person_name in person_names:
        field = "persons.name" if is_nested else "name"
        queries.append(Q("match", **{field: person_name}))
    return queries


def _search_by_role_code_es_query(role_codes: List[str], is_nested: bool):
    if is_nested:
        return Q("terms", persons__role_code=role_codes)
    else:
        return Q("terms", role_code=role_codes)


def _search_by_role_code_groups_es_query(role_group_codes: List[str], is_nested: bool):
    if is_nested:
        return Q("terms", persons__role_group_codes=role_group_codes)
    else:
        return Q("terms", role_group_codes=role_group_codes)


def _search_by_platform_es_query(request: Platform, is_nested: bool):
    fields = ["linkedin", "twitter", "github", "wantedly", "facebook"]
    queries = []
    if request.platforms:
        for p in request.platforms:
            p = p.lower()
            if p in fields:
                if p == "facebook":
                    p = "fb"
                field_path = f"persons.{p}_url" if is_nested else f"{p}_url"
                queries.append(Q("exists", field=field_path))
    bool_query = (
        Q("bool", should=queries)
        if request.operator == "OR"
        else Q("bool", must=queries)
    )
    return bool_query


def _search_by_sns_urls_es_query(sns_urls: List[str], is_nested: bool):
    additional_urls = []

    for url in sns_urls:
        if "x.com" in url:
            twitter_url = url.replace("x.com", "twitter.com")
            if twitter_url not in sns_urls and twitter_url not in additional_urls:
                additional_urls.append(twitter_url)

        if "twitter.com" in url:
            x_url = url.replace("twitter.com", "x.com")
            if x_url not in sns_urls and x_url not in additional_urls:
                additional_urls.append(x_url)

    sns_urls.extend(additional_urls)
    queries = []
    if is_nested:
        queries.extend(
            [Q("wildcard", persons__linkedin_url=f"*{x}*") for x in sns_urls]
        )
        queries.extend([Q("wildcard", persons__twitter_url=f"*{x}*") for x in sns_urls])
        queries.extend([Q("wildcard", persons__github_url=f"*{x}*") for x in sns_urls])
        queries.extend(
            [Q("wildcard", persons__wantedly_url=f"*{x}*") for x in sns_urls]
        )
        queries.extend([Q("wildcard", persons__fb_url=f"*{x}*") for x in sns_urls])
    else:
        queries.extend([Q("wildcard", linkedin_url=f"*{x}*") for x in sns_urls])
        queries.extend([Q("wildcard", twitter_url=f"*{x}*") for x in sns_urls])
        queries.extend([Q("wildcard", github_url=f"*{x}*") for x in sns_urls])
        queries.extend([Q("wildcard", wantedly_url=f"*{x}*") for x in sns_urls])
        queries.extend([Q("wildcard", fb_url=f"*{x}*") for x in sns_urls])
    return Q("bool", should=queries)


def _search_by_uuid_es_query(person_uuids: List[str], is_nested: bool):
    if is_nested:
        return Q("terms", persons__uuid=person_uuids)
    else:
        return Q("terms", uuid=person_uuids)


def _search_by_company_collections_es_query(
    cors: CorporateNumberByCollection,
    collection_list: CollectionList,
    is_nested: bool,
    mode: SearchMode,
):
    queries = []
    if (
        cors.exclude_corporate_numbers
        and collection_list.exclude_collections
        and len(collection_list.exclude_collections)
    ):
        if is_nested:
            exclude_query = Q(
                "bool",
                must_not=Q(
                    "terms", companies__corporate_number=cors.exclude_corporate_numbers
                ),
            )
        else:
            exclude_query = Q(
                "bool",
                must_not=Q("terms", corporate_number=cors.exclude_corporate_numbers),
            )
        queries.append(exclude_query)

    if (
        cors.or_corporate_numbers is not None
        and collection_list.or_collections
        and len(collection_list.or_collections)
    ):
        if is_nested:
            if mode == SearchMode.FUZZY:
                or_query = Q(
                    "terms", companies_fuzzy__corporate_number=cors.or_corporate_numbers
                )
            else:
                or_query = Q(
                    "terms", companies__corporate_number=cors.or_corporate_numbers
                )
        else:
            or_query = Q("terms", corporate_number=cors.or_corporate_numbers)
        queries.append(or_query)
    return queries


def _search_by_person_collections_es_query(
    uuids: UuidsByCollection, collection_list: CollectionList, is_nested: bool
):
    queries = []
    if (
        uuids.exclude_uuids
        and collection_list.exclude_collections
        and len(collection_list.exclude_collections)
    ):
        exclude_query = (
            Q("bool", must_not=Q("terms", persons__uuid=uuids.exclude_uuids))
            if is_nested
            else Q("bool", must_not=Q("terms", uuid=uuids.exclude_uuids))
        )
        queries.append(exclude_query)

    if (
        uuids.or_uuids is not None
        and collection_list.or_collections
        and len(collection_list.or_collections)
    ):
        or_query = (
            Q("terms", persons__uuid=uuids.or_uuids)
            if is_nested
            else Q("terms", uuid=uuids.or_uuids)
        )
        queries.append(or_query)

    return queries


def _search_by_funding_es_query(funding: Funding, is_nested: bool, mode: SearchMode):
    if funding.duration == DurationFunding.THREE_MONTH:
        if is_nested:
            return (
                Q("terms", companies__three_month_funding_flags=funding.funding_stage)
                if mode == SearchMode.EXACT
                else Q(
                    "terms",
                    companies_fuzzy__three_month_funding_flags=funding.funding_stage,
                )
            )
        else:
            return Q("terms", three_month_funding_flags=funding.funding_stage)

    if funding.duration == DurationFunding.SIX_MONTH:
        if is_nested:
            return (
                Q("terms", companies__six_month_funding_flags=funding.funding_stage)
                if mode == SearchMode.EXACT
                else Q(
                    "terms",
                    companies_fuzzy__six_month_funding_flags=funding.funding_stage,
                )
            )
        else:
            return Q("terms", six_month_funding_flags=funding.funding_stage)

    if funding.duration == DurationFunding.ONE_YEAR:
        if is_nested:
            return (
                Q("terms", companies__twelve_month_funding_flags=funding.funding_stage)
                if mode == SearchMode.EXACT
                else Q(
                    "terms",
                    companies_fuzzy__twelve_month_funding_flags=funding.funding_stage,
                )
            )
        else:
            return Q("terms", twelve_month_funding_flags=funding.funding_stage)

    if is_nested:
        return (
            Q("terms", companies__all_funding_flags=funding.funding_stage)
            if mode == SearchMode.EXACT
            else Q("terms", companies_fuzzy__all_funding_flags=funding.funding_stage)
        )
    else:
        return Q("terms", all_funding_flags=funding.funding_stage)


def _search_by_opt_out_es_query(is_nested: bool):
    if is_nested:
        return Q(
            "bool",
            should=[
                Q(
                    "bool",
                    must_not=[
                        Q(
                            "nested",
                            path="persons",
                            query=Q("exists", field="persons.is_opt_out"),
                        )
                    ],
                ),
                Q("bool", must_not=[Q("exists", field="persons")]),
            ],
            minimum_should_match=1,
        )
    else:
        return Q("bool", must_not=[Q("exists", field="is_opt_out")])


def _search_by_company_identified_es_query(
    cors: CorporateNumberByIdentified, is_nested: bool, mode: SearchMode
):
    queries = []
    if cors.or_corporate_numbers is not None:
        if is_nested:
            if mode == SearchMode.FUZZY:
                or_query = Q(
                    "terms", companies_fuzzy__corporate_number=cors.or_corporate_numbers
                )
            else:
                or_query = Q(
                    "terms", companies__corporate_number=cors.or_corporate_numbers
                )
        else:
            or_query = Q("terms", corporate_number=cors.or_corporate_numbers)
        queries.append(or_query)

    return queries


def _search_by_press_release_keyword_es_query(
    keyword: Keyword, is_nested: bool = False
):
    queries = []
    fields = [
        "title^1",
        "sub_title^1",
        "content^0.8",
        "keyword_texts^0.8",
    ]

    def create_multi_match_query(
        keyword: str,
        optimize_keyword: bool = False,
        path: str = None,
        is_exact: bool = False,
    ):
        query_text = optimize_name(keyword) if optimize_keyword else keyword
        query_fields = [f"{path}.{field}" for field in fields] if is_nested else fields
        if is_exact:
            return Q(
                "multi_match",
                query=query_text,
                fields=query_fields,
                type="phrase",
                slop=0,
                lenient=True,
            )
        else:
            return Q(
                "multi_match",
                query=query_text,
                fields=query_fields,
                slop=0,
                lenient=True,
            )

    if keyword.and_keywords:
        and_queries = [
            create_multi_match_query(
                word,
                optimize_keyword=True,
                path="press_releases",
                is_exact=keyword.is_exact,
            )
            for word in keyword.and_keywords
        ]
        queries.append(Q("bool", must=and_queries))

    if keyword.or_keywords:
        or_queries = [
            create_multi_match_query(
                word,
                optimize_keyword=True,
                path="press_releases",
                is_exact=keyword.is_exact,
            )
            for word in keyword.or_keywords
        ]

        queries.append(
            Q(
                "bool",
                should=or_queries,
                minimum_should_match=1,
            )
        )

    if keyword.exclude_keywords:
        exclude_queries = [
            create_multi_match_query(
                word,
                optimize_keyword=True,
                path="press_releases",
                is_exact=keyword.is_exact,
            )
            for word in keyword.exclude_keywords
        ]

        queries.append(
            Q(
                "bool",
                must_not=exclude_queries,  # None of these queries should match (NOT condition)
            )
        )

    return queries


def _search_by_media_codes_es_query(news_media: List[str], is_nested: bool = False):
    if is_nested:
        return Q("terms", press_releases__media_code=news_media)
    else:
        return Q("terms", media_code=news_media)


def _search_by_posted_date_range_es_query(
    posted_date_range_list: List[PostingPeriod],
    is_nested: bool = False,
):
    posting_period_ranges = {
        PostingPeriod.ONE_MONTH: (timedelta(days=30), timedelta(days=0)),
        PostingPeriod.ONE_TO_THREE_MONTH: (timedelta(days=90), timedelta(days=30)),
        PostingPeriod.THREE_TO_SIX_MONTH: (timedelta(days=180), timedelta(days=90)),
        PostingPeriod.SIX_TO_ONE_YEAR: (timedelta(days=365), timedelta(days=180)),
    }
    now = datetime.now()

    posting_period_queries = []
    for period in posted_date_range_list:
        if period in posting_period_ranges:
            delta_start, delta_end = posting_period_ranges[period]
            start_at = now - delta_start
            end_at = now - delta_end
            if is_nested:
                posting_period_queries.append(
                    Q(
                        "range",
                        press_releases__posted_at={
                            "gte": start_at,
                            "lte": end_at,
                        },
                    ),
                )
            else:
                posting_period_queries.append(
                    Q(
                        "range",
                        posted_at={"gte": start_at, "lte": end_at},
                    )
                )
        elif period == PostingPeriod.ONE_YEAR_OR_MORE:
            end_at = now - timedelta(days=365)
            if is_nested:
                posting_period_queries.append(
                    Q(
                        "range",
                        press_releases__posted_at={"lte": end_at},
                    )
                )
            else:
                posting_period_queries.append(
                    Q(
                        "range",
                        posted_at={"lte": end_at},
                    )
                )

    return Q("bool", should=posting_period_queries)


def _search_by_business_categories_es_query(
    business_categories: List[str], is_nested: bool = False
):
    if is_nested:
        return Q(
            "bool",
            should=[
                Q(
                    "wildcard",
                    press_releases__business_category_texts={
                        "value": f"{category}*",
                        "case_insensitive": True,
                    },
                )
                for category in business_categories
            ],
        )
    else:
        return Q("terms", business_category_texts=business_categories)


def _search_by_types_es_query(type_codes: List[str], is_nested: bool = False):
    if is_nested:
        return Q("terms", press_releases__type_code=type_codes)
    else:
        return Q("terms", type_code=type_codes)


def _filter_by_posted_at_es_query(is_nested: bool = False):
    if is_nested:
        return Q(
            "range",
            press_releases__posted_at={"gte": datetime.now() - timedelta(days=180)},
        )
    else:
        return Q("range", posted_at={"gte": datetime.now() - timedelta(days=180)})


def build_press_release_es_query(
    request: SearchPressReleaseRequest,
    is_nested: bool = False,
    categories: List[str] = [],
):
    must_queries = []
    if request.keyword:
        must_queries.extend(
            _search_by_press_release_keyword_es_query(request.keyword, is_nested)
        )

    if request.media:
        must_queries.append(_search_by_media_codes_es_query(request.media, is_nested))

    if request.posting_period:
        must_queries.append(
            _search_by_posted_date_range_es_query(request.posting_period, is_nested)
        )

    if request.business_categories:
        must_queries.append(
            _search_by_business_categories_es_query(categories, is_nested)
        )

    if request.type_codes:
        must_queries.append(_search_by_types_es_query(request.type_codes, is_nested))

    return must_queries


def build_person_es_query(
    request: SearchPersonRequest,
    is_nested: bool = False,
    persons_uuids: List[str] = [],
    persons_csv_uuids: List[str] = [],
):
    person_queries = []

    if request.person_keywords:
        if request.person_keywords.is_exact:
            person_queries.extend(
                _search_by_exact_person_keyword_es_query(
                    request.person_keywords, is_nested
                )
            )
        else:
            person_queries.extend(
                _search_by_person_keyword_es_query(request.person_keywords, is_nested)
            )

    if request.name:
        name_queries = _search_by_name_es_query(
            split_string_by_newline(request.name), is_nested
        )
        person_queries.append(Q("bool", should=name_queries, minimum_should_match=1))

    if request.role_codes:
        person_queries.append(
            _search_by_role_code_es_query(request.role_codes, is_nested)
        )

    if request.role_group_codes:
        person_queries.append(
            _search_by_role_code_groups_es_query(
                translate_roles(request.role_group_codes), is_nested
            )
        )

    if request.sns_url:
        person_queries.append(
            _search_by_sns_urls_es_query(
                split_string_by_newline(request.sns_url), is_nested
            )
        )

    if request.platform:
        person_queries.append(_search_by_platform_es_query(request.platform, is_nested))

    if request.is_persons_unlocked:
        if len(persons_uuids) >= 0:
            person_queries.append(_search_by_uuid_es_query(persons_uuids, is_nested))

    if persons_csv_uuids:
        print("persons_csv_uuids: ", persons_csv_uuids)
        # if len(persons_csv_uuids) > 0:
        #     person_queries.append(
        #         _search_by_uuid_es_query(persons_csv_uuids, is_nested)
        #     )

    if request.uuids_by_collection:
        person_queries.extend(
            _search_by_person_collections_es_query(
                request.uuids_by_collection,
                request.person_collections,
                is_nested,
            )
        )

    if request.person_uuids:
        person_queries.append(_search_by_uuid_es_query(request.person_uuids, is_nested))

    person_queries.append(_search_by_opt_out_es_query(is_nested))

    return person_queries
