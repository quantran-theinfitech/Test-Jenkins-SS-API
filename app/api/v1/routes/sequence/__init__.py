from fastapi import APIRouter

from app.api.base.deps import custom_generate_unique_id

from .campaigns import router as campaign_router
from .campaigns import router as sequence_router
from .contacts import router as contact_router
from .gsuite import router as gsuite_router
from .linkedin_activities import router as linkedin_history_router
from .linkedin_connection import router as linkedin_router
from .mail_histories import router as mail_history_router
from .mail_templates import router as mail_template_router
from .mailboxes import router as mailbox_router
from .message_template import router as message_template_router
from .note_template import router as note_template_router
from .persons import router as person_router
from .schedules import router as schedule_router

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)

routers = [
    campaign_router,
    person_router,
    mail_template_router,
    contact_router,
    sequence_router,
    schedule_router,
    mail_history_router,
    mailbox_router,
    gsuite_router,
    linkedin_router,
    message_template_router,
    note_template_router,
    linkedin_history_router,
]

for router_to_include in routers:
    router.include_router(router_to_include)
