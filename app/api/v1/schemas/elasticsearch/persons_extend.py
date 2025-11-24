from elasticsearch_dsl import (
    Boolean,
    Date,
    Document,
    Double,
    InnerDoc,
    Integer,
    Keyword,
    Long,
    Nested,
    Short,
    Text,
)
from elasticsearch_dsl.connections import connections

from app.api.v1.schemas.elasticsearch import CompanyInnerDoc, PersonInnerDoc
from app.config import settings
from app.es import es_basic_auth

connections.create_connection(
    hosts=[settings.ES_HOST],
    http_auth=es_basic_auth,
    scheme=[settings.ES_SCHEME],
    port=settings.ES_PORT,
)


class ESPersonExtend(Document, PersonInnerDoc):
    companies = Nested(CompanyInnerDoc, multi=True)
    companies_fuzzy = Nested(CompanyInnerDoc, multi=True)

    class Index:
        name = "person-extend-current"
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

    # @classmethod
    # def init(cls, index=None, using=None):
    #     cls._doc_type.mapping.meta(name="_source", params=
    #         dict(
    #             excludes=[
    #                 "bio",
    #                 "companies",
    #                 "intro",
    #                 "updated_at",
    #                 "companies_fuzzy.all_funding_flags",
    #                 "companies_fuzzy.average_age",
    #                 "companies_fuzzy.business_content",
    #                 "companies_fuzzy.business_html_content",
    #                 "companies_fuzzy.business_model_codes",
    #                 "companies_fuzzy.capital",
    #                 "companies_fuzzy.closing_month",
    #                 "companies_fuzzy.communication_tools",
    #                 "companies_fuzzy.contact_email",
    #                 "companies_fuzzy.contact_form_url",
    #                 "companies_fuzzy.crm_tools",
    #                 "companies_fuzzy.domain",
    #                 "companies_fuzzy.employees_count",
    #                 "companies_fuzzy.english_name",
    #                 "companies_fuzzy.establish_at",
    #                 "companies_fuzzy.fax",
    #                 "companies_fuzzy.hp_url",
    #                 "companies_fuzzy.industry_code",
    #                 "companies_fuzzy.info_html_content",
    #                 "companies_fuzzy.internal_tools",
    #                 "companies_fuzzy.kana_name",
    #                 "companies_fuzzy.landing_html_content",
    #                 "companies_fuzzy.latest_parttime_recruit_at",
    #                 "companies_fuzzy.latest_recruits_at",
    #                 "companies_fuzzy.listing_market_code",
    #                 "companies_fuzzy.management_tools",
    #                 "companies_fuzzy.nta_city_id",
    #                 "companies_fuzzy.nta_prefecture_id",
    #                 "companies_fuzzy.original_tags",
    #                 "companies_fuzzy.phone",
    #                 "companies_fuzzy.president_name",
    #                 "companies_fuzzy.press_release_media_codes",
    #                 "companies_fuzzy.recruit_email",
    #                 "companies_fuzzy.recruit_phone",
    #                 "companies_fuzzy.revenue",
    #                 "companies_fuzzy.six_month_funding_flags",
    #                 "companies_fuzzy.sub_industries_code",
    #                 "companies_fuzzy.tech_clouds",
    #                 "companies_fuzzy.tech_databases",
    #                 "companies_fuzzy.tech_frameworks",
    #                 "companies_fuzzy.tech_languages",
    #                 "companies_fuzzy.technologies",
    #                 "companies_fuzzy.three_month_funding_flags",
    #                 "companies_fuzzy.twelve_month_funding_flags"
    #             ]
    #         )
    #     )
    #     super().init(index=index, using=using)
    def save(self, **kwargs):
        return super().save(**kwargs)
