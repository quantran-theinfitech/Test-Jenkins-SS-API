import pandas as pd
from fastapi.responses import PlainTextResponse


def download_contacts_template_csv():

    temp_df = pd.DataFrame(
        data={
            "name": [],
            "bio": [],
            "email": [],
            "address": [],
            "skills": [],
            "company_name": [],
            "status_code": [],
            "linkedin_url": [],
            "twitter_url": [],
            "github_url": [],
            "note_url": [],
            "contact_times": [],
            "inbox_times": [],
            "potential_action_at": [],
            "site_usage_at": [],
            "change_history_at": [],
            "lead_source_code": [],
            "fb_url": [],
        }
    )

    return PlainTextResponse(
        temp_df.to_csv(index=False),
        media_type="text/plain;charset=UTF-8",
        headers={"Content-Disposition": "attachment"},
    )
