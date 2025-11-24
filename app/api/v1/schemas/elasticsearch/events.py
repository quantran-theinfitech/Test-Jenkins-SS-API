from elasticsearch_dsl import Date, Document, Keyword, Text
from elasticsearch_dsl.connections import connections

from app.config import settings
from app.es import es_basic_auth

# Kết nối Elasticsearch
connections.create_connection(
    hosts=[settings.ES_HOST],
    http_auth=es_basic_auth,
    scheme=[settings.ES_SCHEME],
    port=settings.ES_PORT,
)


class ESEvent(Document):
    id = Keyword()
    name = Text(analyzer="name_index_analyzer", search_analyzer="name_search_analyzer")
    content = Text(analyzer="jp_analyzer", search_analyzer="jp_analyzer")
    corporate_number = Keyword()
    media_internal_id = Keyword()
    media_code = Keyword()
    source_event_url = Keyword()
    ingest_id = Keyword()
    start_time = Date()
    end_time = Date()
    type = Keyword()
    address = Text(analyzer="jp_analyzer", search_analyzer="jp_analyzer")
    created_at = Date()
    updated_at = Date()

    class Index:
        name = "events"
        settings = {
            "analysis": {
                "char_filter": {
                    "normalize": {
                        "type": "icu_normalizer",
                        "name": "nfkc",
                        "mode": "compose",
                    }
                },
                "analyzer": {
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
