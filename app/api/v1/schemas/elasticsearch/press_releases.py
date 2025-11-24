from elasticsearch_dsl import (
    Boolean,
    Date,
    Document,
    Double,
    Integer,
    Keyword,
    Long,
    Object,
    Short,
    Text,
)
from elasticsearch_dsl.connections import connections

from app.config import settings
from app.es import es_basic_auth

connections.create_connection(
    hosts=[settings.ES_HOST],
    http_auth=es_basic_auth,
    scheme=[settings.ES_SCHEME],
    port=settings.ES_PORT,
)


class ESPressRelease(Document):
    ingest_id = Keyword()
    media_internal_id = Keyword()
    media_code = Keyword()
    source_article_url = Keyword()
    corporate_number = Keyword()
    company_name = Text(
        analyzer="name_index_analyzer", search_analyzer="name_search_analyzer"
    )

    type_code = Keyword()
    title = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    sub_title = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    content = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    body_urls = Keyword(multi=True)
    business_category_texts = Keyword(multi=True)
    business_category_urls = Keyword(multi=True)
    prtimes_location_info_texts = Keyword(multi=True)
    prtimes_location_info_urls = Keyword(multi=True)
    keyword_texts = Keyword(multi=True)
    keyword_urls = Keyword(multi=True)

    posted_at_raw = Text()
    posted_at = Date()
    article_company_id = Keyword()

    # company
    companies = Object(
        properties={
            "establish_at": Date(),
            "establish_time_level": Keyword(),
            "name": Text(
                analyzer="name_index_analyzer", search_analyzer="name_search_analyzer"
            ),
            "kana_name": Text(
                analyzer="name_index_analyzer", search_analyzer="name_search_analyzer"
            ),
            "english_name": Text(),
            "postal_code": Keyword(),
            "nta_city_id": Integer(),
            "nta_prefecture_id": Integer(),
            "address": Text(search_analyzer="jp_analyzer"),
            "corporate_number": Keyword(),
            "corporate_kind": Short(),
            "nta_closed_Date": Date(),
            "nta_closed_reason": Keyword(),
            "nta_updated_at": Date(),
            "nta_created_at": Date(),
            "hp_url": Keyword(),
            "domain": Keyword(),
            "president_name": Keyword(),
            "president_dob": Date(),
            "factories_count": Integer(),
            "branches_count": Integer(),
            "headquarters_count": Integer(),
            "industry_code": Keyword(),
            "main_sub_industry_code": Keyword(),
            "sub_industries_code": Keyword(multi=True),
            "business_content": Text(
                search_analyzer="jp_analyzer", analyzer="jp_analyzer"
            ),
            "listing_market_code": Keyword(),
            "listing_year": Short(),
            "listing_time_code": Keyword(),
            "revenue_change": Integer(),
            "employee_change": Integer(),
            "revenue_change_rate": Double(),
            "youtube_url": Keyword(),
            "twitter_url": Keyword(),
            "facebook_url": Keyword(),
            "linkedin_url": Keyword(),
            "contact_form_url": Keyword(),
            "president_university": Keyword(),
            "revenue": Long(),
            "revenue_ai": Long(),
            "revenue_raw": Text(),
            "recruit_phone": Keyword(),
            "sub_companies_count": Integer(),
            "phone": Keyword(),
            "recruit_email": Keyword(),
            "contact_email": Keyword(),
            "capital_adequacy_ratio": Double(),
            "capital": Long(),
            "capital_raw": Text(),
            "capital_change": Integer(),
            "average_work_duration": Double(),
            "fax": Keyword(),
            "closing_month": Short(),
            "employee_change_rate": Double(),
            "employees_count": Integer(),
            "average_age": Double(),
            "average_salary": Integer(),
            "latest_recruits_at": Date(),
            "this_month_recruits_count": Integer(),
            "this_month_doda_recruits_count": Integer(),
            "this_month_mynavi_tenshoku_recruits_count": Integer(),
            "latest_press_release_at": Date(),
            "this_month_prtimes_count": Integer(),
            "this_month_value_press_count": Integer(),
            "display_flag": Short(),
            "created_at": Date(),
            "updated_at": Date(),
            "meta_title": Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer"),
            "meta_description": Text(
                search_analyzer="jp_analyzer", analyzer="jp_analyzer"
            ),
            "meta_keywords": Text(
                search_analyzer="jp_analyzer", analyzer="jp_analyzer"
            ),
            "raw_industries": Keyword(multi=True),
            "press_release_media_codes": Keyword(multi=True),
            "recruit_media_codes": Keyword(multi=True),
            "tool_codes": Keyword(multi=True),
            "one_month_employee_delta": Short(),
            "three_month_employee_delta": Short(),
            "six_month_employee_delta": Short(),
            "one_year_employee_delta": Short(),
            "one_month_capital_delta": Long(),
            "three_month_capital_delta": Long(),
            "six_month_capital_delta": Long(),
            "one_year_capital_delta": Long(),
            "one_month_revenue_delta": Long(),
            "three_month_revenue_delta": Long(),
            "six_month_revenue_delta": Long(),
            "one_year_revenue_delta": Long(),
            "latest_new_graduate_recruit_at": Date(),
            "latest_middle_recruit_at": Date(),
            "latest_parttime_recruit_at": Date(),
            "employment_type_codes": Keyword(multi=True),
            "recruit_features": Keyword(multi=True),
            "occupation_codes": Keyword(multi=True),
            "raw_occupations": Keyword(multi=True),
            "skill_codes": Keyword(multi=True),
            "group_employee_count": Integer(),
            "main_customers": Text(),
            "group_companies": Text(),
            "market_capitalization_raw": Text(),
            "market_capitalization": Long(),
            "address_latitude": Long(),
            "address_longitude": Long(),
            "recruit_tags": Keyword(multi=True),
            "recruit_qualifications": Keyword(multi=True),
            "tech_languages": Keyword(multi=True),
            "tech_frameworks": Keyword(multi=True),
            "tech_clouds": Keyword(multi=True),
            "tech_databases": Keyword(multi=True),
            "communication_tools": Keyword(multi=True),
            "management_tools": Keyword(multi=True),
            "internal_tools": Keyword(multi=True),
            "crm_tools": Keyword(multi=True),
            "business_model_codes": Keyword(multi=True),
            "contact_ng_flag": Boolean(),
            "contact_sales_ng_flag": Boolean(),
            "contact_info_ng_flag": Boolean(),
            "display_ng_flag": Boolean(),
            "three_month_funding_flags": Keyword(multi=True),
            "six_month_funding_flags": Keyword(multi=True),
            "twelve_month_funding_flags": Keyword(multi=True),
            "all_funding_flags": Keyword(multi=True),
            "business_html_content": Text(
                search_analyzer="jp_analyzer", analyzer="jp_analyzer"
            ),
            "landing_html_content": Text(
                search_analyzer="jp_analyzer", analyzer="jp_analyzer"
            ),
            "info_html_content": Text(
                search_analyzer="jp_analyzer", analyzer="jp_analyzer"
            ),
            "original_tags": Keyword(multi=True),
        }
    )

    class Index:
        name = "press-release"
        settings = {
            "analysis": {
                "char_filter": {
                    "normalize": {
                        "type": "icu_normalizer",
                        "name": "nfkc",
                        "mode": "compose",
                    }
                },
                "tokenizer": {
                    "name_index_tokenizer": {
                        "mode": "search",
                        "type": "kuromoji_tokenizer",
                    },
                    "name_search_tokenizer": {
                        "mode": "normal",
                        "type": "kuromoji_tokenizer",
                    },
                },
                "analyzer": {
                    "name_index_analyzer": {
                        "type": "custom",
                        "char_filter": ["normalize"],
                        "tokenizer": "name_index_tokenizer",
                        "filter": [
                            "cjk_width",
                            "kuromoji_stemmer",
                            "lowercase",
                        ],
                    },
                    "name_search_analyzer": {
                        "type": "custom",
                        "char_filter": ["normalize"],
                        "tokenizer": "name_search_tokenizer",
                        "filter": [
                            "cjk_width",
                            "kuromoji_stemmer",
                            "lowercase",
                        ],
                    },
                    "jp_analyzer": {
                        "type": "custom",
                        "char_filter": ["normalize"],
                        "tokenizer": "standard",
                        "filter": [
                            "kuromoji_baseform",
                            "kuromoji_part_of_speech",
                            "cjk_width",
                            "ja_stop",
                            "kuromoji_stemmer",
                            "lowercase",
                        ],
                    },
                },
            },
        }

    def save(self, **kwargs):
        return super().save(**kwargs)
