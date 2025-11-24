from pathlib import Path
from typing import Generator

from elasticsearch import AsyncElasticsearch, Elasticsearch
from fastapi.routing import APIRoute
from fastapi_mail import ConnectionConfig
from redis import Redis
from sqlmodel import Session

from app.config import settings
from app.db import engine
from app.es import es_basic_auth, es_url
from app.redis import redis_host, redis_port


def get_db():
    with Session(engine) as session:
        yield session


def get_es():
    with Elasticsearch(
        hosts=[es_url], http_auth=es_basic_auth, timeout=60
    ) as elasticsearch:
        yield elasticsearch


async def get_es_async():
    async with AsyncElasticsearch(
        hosts=[es_url],
        http_auth=es_basic_auth,
        timeout=60,
    ) as elasticsearch:
        yield elasticsearch


def get_session() -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def mail_connection():
    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        TEMPLATE_FOLDER=Path(__file__).parent.parent / "v1/templates",
    )


def custom_generate_unique_id(route: APIRoute) -> str:
    return route.name


def get_redis_service() -> Generator[Redis, None, None]:
    with Redis(
        host=redis_host, port=int(redis_port), ssl=False
    ) as redis:
        yield redis
