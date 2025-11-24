from elasticsearch_dsl import (
    Boolean,
    Date,
    Document,
    Integer,
    Keyword,
    Nested,
    Object,
    Text,
)
from elasticsearch_dsl.connections import connections

from app.api.v1.schemas.elasticsearch import CompanyInnerDoc
from app.config import settings
from app.es import es_basic_auth

connections.create_connection(
    hosts=[settings.ES_HOST],
    http_auth=es_basic_auth,
    scheme=[settings.ES_SCHEME],
    port=settings.ES_PORT,
)


class ESRecruit(Document):
    ingest_id = Keyword()
    media_internal_id = Keyword()
    media_code = Keyword()
    source_recruit_url = Keyword()
    corporate_number = Keyword()
    company_name = Text(
        analyzer="name_index_analyzer", search_analyzer="name_search_analyzer"
    )
    title = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    sub_title = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    explain = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    content = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    summary = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    employment_type_codes = Keyword(multi=True)
    recruit_tels = Keyword(multi=True)
    recruit_mails = Keyword(multi=True)
    working_address_list = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    working_location = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    working_time = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    application_contacts = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    application_flow = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    recruitment_count = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    recruit_sales_approach_reject_flag = Boolean()
    remote_flag = Boolean()
    full_remote_flag = Boolean()
    required_educational_flag = Boolean()
    required_college_flag = Boolean()
    required_university_graduate_flag = Boolean()
    required_post_graduate_flag = Boolean()
    allow_sidejob_flag = Boolean()
    online_interview_flag = Boolean()
    attitude_test_flag = Boolean()
    salary_year_min = Integer()
    salary_year_max = Integer()
    salary_year_value = Integer()
    salary_month_min = Integer()
    salary_month_max = Integer()
    salary_month_value = Integer()
    salary_day_min = Integer()
    salary_day_max = Integer()
    salary_day_value = Integer()
    salary_hour_min = Integer()
    salary_hour_max = Integer()
    salary_hour_value = Integer()
    salary_raw = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    welfare_benefit = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    holiday = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    tags = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    search_keywords = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    job_recruit_qualifications = Keyword(multi=True)
    job_skill_codes = Keyword(multi=True)
    job_tech_languages = Keyword(multi=True)
    job_tech_frameworks = Keyword(multi=True)
    job_tech_clouds = Keyword(multi=True)
    job_tech_databases = Keyword(multi=True)
    job_communication_tools = Keyword(multi=True)
    job_management_tools = Keyword(multi=True)
    job_internal_tools = Keyword(multi=True)
    job_crm_tools = Keyword(multi=True)
    search_keywords = Keyword(multi=True)
    large_category = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    medium_category = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    small_category = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    prefecture_codes = Integer(multi=True)
    city_codes = Integer(multi=True)
    start_at = Date()
    end_at = Date()
    job_company_id = Keyword()
    other_info = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    job_positions = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    scores = Keyword(multi=True)
    categories = Keyword(multi=True)
    sub_categories = Keyword(multi=True)
    category_codes = Keyword(multi=True)
    sub_category_codes = Keyword(multi=True)
    application_flow_codes = Keyword(multi=True)
    holiday_codes = Keyword(multi=True)
    holiday_year_min = Integer()
    holiday_year_max = Integer()

    categories_positions = Nested(
        properties={
            "category_code": Keyword(),
            "sub_category_code": Keyword(),
            "position": Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer"),
        }
    )

    # company

    companies = Object(CompanyInnerDoc)

    class Index:
        name = "recruit"
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
