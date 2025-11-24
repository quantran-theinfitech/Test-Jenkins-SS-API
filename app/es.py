from app.config import settings

es_url = f"{settings.ES_SCHEME}://{settings.ES_HOST}:{settings.ES_PORT}"
es_basic_auth = (settings.ES_USERNAME, settings.ES_PASSWORD)
