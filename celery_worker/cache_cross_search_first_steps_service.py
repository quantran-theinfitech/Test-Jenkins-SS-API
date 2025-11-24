import json
import time

from elasticsearch import AsyncElasticsearch
from redis import Redis

from app.config import settings


async def _execute_es_search(
    es_client: AsyncElasticsearch,
    query,
    page: int,
):
    from app.api.v1.schemas.elasticsearch.companies_extend import EsCompanyExtend

    search_body = {
        "query": query,
        "size": 1900 if page == 1 else 1000,
        "from": page * 1000,
        "track_total_hits": False,
        "_source": ["corporate_number"],
    }

    return await es_client.search(
        index=EsCompanyExtend.Index.name,
        body=search_body,
    )


async def _execute_page_with_retry(
    es_client: AsyncElasticsearch,
    query,
    page: int,
    cache_key: str,
):
    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = await _execute_es_search(es_client, query, page)

            hits = response.get("hits", {}).get("hits", [])
            if not hits:
                return []

            companies = [hit["_source"] for hit in hits]
            return [company["corporate_number"] for company in companies]
        except Exception:
            if attempt == max_retries - 1:
                return []
            else:
                time.sleep(0.5 * (attempt + 1))

    return []


async def cache_cross_search_first_steps_service(
    es_client: AsyncElasticsearch,
    redis_client: Redis,
    query: dict,
    cache_key: str,
):
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            if isinstance(cached_data, bytes):
                cached_data = cached_data.decode("utf-8")
            try:
                cached_data = json.loads(str(cached_data))
            except json.JSONDecodeError:
                cached_data = str(cached_data)
            all_corporate_numbers = cached_data.get("data", [])
        else:
            all_corporate_numbers = []

        completed_pages = 0
        has_error = False

        for page in range(1, 10):
            try:
                page_data = await _execute_page_with_retry(
                    es_client, query, page, cache_key
                )

                if page_data:
                    all_corporate_numbers.extend(page_data)
                    completed_pages += 1

                    updated_cache = {
                        "data": all_corporate_numbers,
                        "error": has_error,
                        "is_finished": completed_pages >= 9,
                        "completed_pages": completed_pages,
                    }
                    redis_client.setex(
                        cache_key,
                        settings.REDIS_CACHE_TTL,
                        json.dumps(updated_cache, ensure_ascii=False, default=str),
                    )

            except Exception:
                has_error = True

        final_cache = {
            "data": all_corporate_numbers,
            "error": has_error,
            "is_finished": True,
        }
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            json.dumps(final_cache, ensure_ascii=False, default=str),
        )
        print(
            f"""Background fetch completed - {cache_key}:
                {len(all_corporate_numbers)} records, error: {has_error}"""
        )

    except Exception as e:
        redis_client.delete(cache_key)
        print(f"Background fetch error for cache key {cache_key}: {e}")
