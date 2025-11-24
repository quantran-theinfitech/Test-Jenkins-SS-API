import json
import logging
from typing import Any, Optional

from redis import Redis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

    def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        try:
            if isinstance(value, str):
                serialized_value = value
            else:
                serialized_value = json.dumps(value, ensure_ascii=False, default=str)

            if expire_seconds:
                result = self.redis_client.setex(key, expire_seconds, serialized_value)
            else:
                result = self.redis_client.setex(
                    key, settings.REDIS_CACHE_TTL, serialized_value
                )

            return result is True
        except Exception as e:
            logger.error(f"Error setting Redis key {key}: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        try:
            value = self.redis_client.get(key)

            if value is None:
                return default

            if isinstance(value, bytes):
                value = value.decode("utf-8")

            value_str = str(value)

            try:
                return json.loads(value_str)
            except (json.JSONDecodeError, TypeError):
                return value_str

        except Exception as e:
            logger.error(f"Error getting Redis key {key}: {e}")
            return default

    def update(
        self, key: str, value: Any, expire_seconds: Optional[int] = None
    ) -> bool:
        try:
            if isinstance(value, dict):
                existing_value = self.get(key)
                if isinstance(existing_value, dict):
                    existing_value.update(value)
                    value = existing_value

            return self.set(key, value, expire_seconds)

        except Exception as e:
            logger.error(f"Error updating Redis key {key}: {e}")
            return False

    def delete(self, key: str):
        try:
            return self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting Redis key {key}: {e}")
            return False
