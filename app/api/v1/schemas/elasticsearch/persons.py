from elasticsearch_dsl import Document, Integer, Keyword, Text
from elasticsearch_dsl.connections import connections

from app.config import settings
from app.es import es_basic_auth

connections.create_connection(
    hosts=[settings.ES_HOST],
    http_auth=es_basic_auth,
    scheme=[settings.ES_SCHEME],
    port=settings.ES_PORT,
)


class ESPerson(Document):
    id = Integer()
    name = Text(search_analyzer="jp_analyzer")
    uuid = Keyword()
    intro = Text(search_analyzer="jp_analyzer")
    role_name = Text(search_analyzer="jp_analyzer")
    bio = Text(search_analyzer="jp_analyzer")
    role_code = Keyword()
    role_group_codes = Keyword(multi=True)
    email = Keyword()
    linkedin_url = Keyword()
    wantedly_url = Keyword()
    twitter_url = Keyword()
    github_url = Keyword()
    note_url = Keyword()
    fb_url = Keyword()
    skills = Text(search_analyzer="jp_analyzer")
    wantedly_id = Keyword()
    linkedin_internal_id = Keyword()
    address = Text(search_analyzer="jp_analyzer")

    corporate_number = Keyword(multi=True)
    company_name = Text(
        analyzer="name_index_analyzer", search_analyzer="name_search_analyzer"
    )
    team_ids = Integer(multi=True)

    class Index:
        name = "person"
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
