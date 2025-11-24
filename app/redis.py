from app.config import settings

redis_host = settings.REDIS_HOST or "redis"
redis_port = settings.REDIS_PORT or "6379"
