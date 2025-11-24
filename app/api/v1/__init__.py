from fastapi import APIRouter

from app.api.v1.routes import (
    activity_logs,
    auth,
    chat,
    companies,
    company_collections,
    connections,
    contacts,
    credits,
    dashboard,
    enrichments,
    events,
    exclude_collections,
    export_histories,
    extensions,
    form_jobs,
    form_schedule,
    form_templates,
    groups,
    healthy,
    hubspot,
    integration,
    investor_relations,
    items,
    mail_templates,
    media,
    person_collections,
    person_exclude_collections,
    persons,
    placeholders,
    plans,
    press_releases,
    recruits,
    scenarios,
    search_all,
    search_conditions,
    search_histories,
    sequence,
    services,
    shorten_path,
    teams,
    todos,
    tracking_urls,
    users,
    youtube_videos,
)

router = APIRouter()
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(companies.router, prefix="/companies", tags=["companies"])
router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
router.include_router(
    company_collections.router,
    prefix="/companies-collections",
    tags=["company-collections"],
)
router.include_router(groups.router, prefix="/groups", tags=["groups"])
router.include_router(teams.router, prefix="/teams", tags=["teams"])
router.include_router(
    activity_logs.router, prefix="/activity-logs", tags=["activity_logs"]
)
router.include_router(items.router, prefix="/items", tags=["items"])
router.include_router(todos.router, prefix="/todos", tags=["todos"])
router.include_router(form_jobs.router, prefix="/form-jobs", tags=["form-jobs"])
router.include_router(
    form_templates.router, prefix="/form-templates", tags=["form_templates"]
)
router.include_router(
    mail_templates.router, prefix="/mail-templates", tags=["mail_templates"]
)
router.include_router(
    placeholders.router, prefix="/placeholders", tags=["placeholders"]
)
router.include_router(
    search_conditions.router, prefix="/search-conditions", tags=["search-conditions"]
)
router.include_router(extensions.router, prefix="/extensions", tags=["extensions"])
router.include_router(
    press_releases.router, prefix="/press-releases", tags=["press-releases"]
)
router.include_router(credits.router, prefix="/credits", tags=["credits"])
router.include_router(recruits.router, prefix="/recruits", tags=["recruits"])
router.include_router(
    exclude_collections.router,
    prefix="/exclude-collections",
    tags=["exclude-collections"],
)
router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["dashboard"],
)

router.include_router(
    healthy.router,
    prefix="/healthy",
    tags=["healthy"],
)
router.include_router(
    tracking_urls.router, prefix="/tracking-urls", tags=["tracking-urls"]
)
router.include_router(
    person_collections.router, prefix="/person-collections", tags=["person_collections"]
)
router.include_router(
    person_exclude_collections.router,
    prefix="/person-exclude-collections",
    tags=["person_exclude_collections"],
)
router.include_router(persons.router, prefix="/persons", tags=["persons"])
router.include_router(connections.router, prefix="/connections", tags=["connections"])
router.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
router.include_router(
    shorten_path.router, prefix="/shorten_path", tags=["shorten_path"]
)
router.include_router(hubspot.router, prefix="/hubspot", tags=["hubspot"])
router.include_router(sequence.router, prefix="/sequence", tags=["sequence"])
router.include_router(integration.router, prefix="/integration", tags=["integration"])
router.include_router(plans.router, prefix="/plans", tags=["plans"])
router.include_router(events.router, prefix="/events", tags=["events"])
router.include_router(services.router, prefix="/services", tags=["services"])
router.include_router(
    export_histories.router, prefix="/export-histories", tags=["export-histories"]
)
router.include_router(enrichments.router, prefix="/enrichments", tags=["enrichments"])
router.include_router(
    form_schedule.router, prefix="/form-schedule", tags=["form-schedule"]
)
router.include_router(
    youtube_videos.router, prefix="/youtube-videos", tags=["youtube-videos"]
)
router.include_router(media.router, prefix="/media", tags=["media"])
router.include_router(search_all.router, prefix="/search-all", tags=["search-all"])
router.include_router(investor_relations.router, prefix="/investor-relations", tags=["investor-relations"])
router.include_router(
    search_histories.router, prefix="/search-histories", tags=["search-histories"]
)