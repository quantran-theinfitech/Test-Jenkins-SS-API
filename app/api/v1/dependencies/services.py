from elasticsearch import AsyncElasticsearch, Elasticsearch
from fastapi import BackgroundTasks, Depends
from redis import Redis
from sqlmodel import Session

from app.api.base.deps import get_es, get_es_async, get_redis_service, get_session
from app.api.v1.dependencies.authentication import get_current_user
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.activity_logs_service import ActivityLogsService
from app.api.v1.services.cross_search_service import CrossSearchService
from app.api.v1.services.extensions import ExtensionService
from app.api.v1.services.form_job_service import FormJobService
from app.api.v1.services.form_template_service import FormTemplateService
from app.api.v1.services.group_service import GroupService
from app.api.v1.services.mail_template_service import MailTemplateService
from app.api.v1.services.placeholder import PlaceholderService
from app.api.v1.services.press_release_service import PressReleaseService
from app.api.v1.services.redis import RedisService
from app.api.v1.services.search_condition_service import SearchConditionService
from app.api.v1.services.team_service import TeamService


def get_group_service(db: Session = Depends(get_session)):
    return GroupService(db)


def get_team_service(db: Session = Depends(get_session)):
    return TeamService(db)


def get_activity_logs_service(db: Session = Depends(get_session)):
    return ActivityLogsService(db)


def get_form_template_service(db: Session = Depends(get_session)):
    return FormTemplateService(db)


def get_mail_template_service(db: Session = Depends(get_session)):
    return MailTemplateService(db)


def get_placeholder_sevice(db: Session = Depends(get_session)):
    return PlaceholderService(db)


def get_search_condition_service(db: Session = Depends(get_session)):
    return SearchConditionService(db)


def get_form_job_service(db: Session = Depends(get_session)):
    return FormJobService(db)


def get_extension_service(db: Session = Depends(get_session)):
    return ExtensionService(db)


def get_press_release_service(db: Session = Depends(get_session)):
    return PressReleaseService(db)


def get_redis_service_impl(
    redis_client: Redis = Depends(get_redis_service),
):
    return RedisService(redis_client)


def get_redis_service_impl(
    redis_client: Redis = Depends(get_redis_service),
):
    return RedisService(redis_client)


def get_cross_search_service(
    es_client: Elasticsearch = Depends(get_es),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user),
    es_async_client: AsyncElasticsearch = Depends(get_es_async),
    redis_service: RedisService = Depends(get_redis_service_impl),
    background_task: BackgroundTasks = BackgroundTasks(),
):
    return CrossSearchService(
        es_client, db, current_user, es_async_client, redis_service, background_task
    )
