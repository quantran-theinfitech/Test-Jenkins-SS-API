import sys

import sentry_sdk

from app.config import settings
from batch.hubspot_pull_companies import hubspot_pull_companies
from batch.hubspot_pull_person import hubspot_pull_persons
from batch.hubspot_push_companies import hubspot_push_companies
from batch.hubspot_sync_companies import hubspot_sync_companies
from batch.salesforce_pull_companies import salesforce_pull_companies
from batch.salesforce_pull_persons import salesforce_pull_persons
from batch.salesforce_push_companies import salesforce_push_companies
from batch.salesforce_sync_companies import salesforce_sync_companies
from batch.sequence_schedule_tasks import handle_sequence_schedule_tasks

COMMAND_HANDLER_FUNC = {
    "hubspot_push_companies": hubspot_push_companies,
    "hubspot_pull_companies": hubspot_pull_companies,
    "hubspot_sync_companies": hubspot_sync_companies,
    "hubspot_pull_persons": hubspot_pull_persons,
    "handle_sequence_schedule_task": handle_sequence_schedule_tasks,
    "salesforce_push_companies": salesforce_push_companies,
    "salesforce_pull_companies": salesforce_pull_companies,
    "salesforce_sync_companies": salesforce_sync_companies,
    "salesforce_pull_persons": salesforce_pull_persons,
}


def handler():
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            # Add request headers and IP for users,
            # see
            # https://docs.sentry.io/platforms/python/data-management/data-collected/
            # for more info
            send_default_pii=True,
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for tracing.
            traces_sample_rate=1.0,
            # To collect profiles for all profile sessions,
            # set `profile_session_sample_rate` to 1.0.
            profile_session_sample_rate=1.0,
            # Profiles will be automatically collected while
            # there is an active span.
            profile_lifecycle="trace",
            environment=settings.SENTRY_ENV,
        )
    arguments = sys.argv[1:]
    if len(arguments) < 1:
        print("No arguments")
        return

    command = arguments[0]
    if command not in COMMAND_HANDLER_FUNC:
        print("Wrong command")
        return
    print("START HANDLE COMMAND")
    with sentry_sdk.start_transaction(name=command, op=command) as transaction:
        COMMAND_HANDLER_FUNC[command](arguments[1:])
        transaction.set_status("ok")
    print("FINISH HANDLE COMMAND")
    return


handler()
