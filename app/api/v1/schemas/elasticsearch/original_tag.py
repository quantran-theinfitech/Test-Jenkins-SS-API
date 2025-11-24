from elasticsearch_dsl import Document, Text
from elasticsearch_dsl.connections import connections

from app.config import settings
from app.es import es_basic_auth

connections.create_connection(
    hosts=[settings.ES_HOST],
    http_auth=es_basic_auth,
    scheme=[settings.ES_SCHEME],
    port=settings.ES_PORT,
)


class EsOriginalTag(Document):
    tag = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")

    class Index:
        name = "original-tag"
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
        return Document.save(self, **kwargs)
