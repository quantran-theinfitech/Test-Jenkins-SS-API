from elasticsearch_dsl import Boolean, Date, Document, Integer, Keyword, Nested, Text
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


class EsCompanyExtend(Document, CompanyInnerDoc):
    team_ids = Integer(multi=True)  # use to unlock company
    persons = Nested(PersonInnerDoc)
    # Nested recruits structure
    recruits = Nested(
        properties={
            "media_code": Keyword(),
            "media_internal_id": Keyword(),
            "title": Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer"),
            "sub_title": Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer"),
            "content": Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer"),
            "employment_type_codes": Keyword(multi=True),
            "search_keywords": Keyword(multi=True),
            "large_category": Text(
                search_analyzer="jp_analyzer", analyzer="jp_analyzer"
            ),
            "medium_category": Text(
                search_analyzer="jp_analyzer", analyzer="jp_analyzer"
            ),
            "small_category": Text(
                search_analyzer="jp_analyzer", analyzer="jp_analyzer"
            ),
            "start_at": Date(),
            "end_at": Date(),
            "tags": Keyword(multi=True),
            "positions": Keyword(multi=True),
            "categories": Keyword(multi=True),
            "sub_categories": Keyword(multi=True),
            "category_codes": Keyword(multi=True),
            "sub_category_codes": Keyword(multi=True),
            "working_location": Text(
                search_analyzer="jp_analyzer", analyzer="jp_analyzer"
            ),
            "working_address_list": Text(
                search_analyzer="jp_analyzer", analyzer="jp_analyzer"
            ),
            "application_flow_codes": Keyword(multi=True),
            "holiday_codes": Keyword(multi=True),
            "holiday_year_min": Integer(),
            "holiday_year_max": Integer(),
            "required_educational_flag": Boolean(),
            "required_college_flag": Boolean(),
            "required_university_graduate_flag": Boolean(),
            "required_post_graduate_flag": Boolean(),
            "salary_year_min": Integer(),
            "salary_year_max": Integer(),
            "salary_year_value": Integer(),
            "salary_month_min": Integer(),
            "salary_month_max": Integer(),
            "salary_month_value": Integer(),
            "job_skill_codes": Keyword(multi=True),
            "job_tech_languages": Keyword(multi=True),
            # "prefecture_codes": Integer(multi=True),
            # "city_codes": Integer(multi=True),
            "job_tech_frameworks": Keyword(multi=True),
            "recruit_qualifications": Keyword(multi=True),
        }
    )

    # Nested press releases structure
    press_releases = Nested(
        properties={
            "media_code": Keyword(),
            "media_internal_id": Keyword(),
            "type_code": Keyword(),
            "title": Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer"),
            "sub_title": Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer"),
            "content": Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer"),
            "business_category_texts": Keyword(multi=True),
            "keyword_texts": Keyword(multi=True),
            "posted_at": Date(),
        }
    )

    class Index:
        name = "company-extend-current"
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
    #     cls._doc_type.mapping.meta(
    #         name="_source",
    #         params=dict(
    #             excludes=[
    #                 "info_html_content",
    #                 "business_html_content",
    #                 "landing_html_content",
    #                 "recruits",
    #                 "press_releases",
    #                 "technologies",
    #             ]
    #         ),
    #     )
    #     super().init(index=index, using=using)
    def save(self, **kwargs):
        return Document.save(self, **kwargs)
