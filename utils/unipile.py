# flake8: noqa: E501

import re
from typing import Any, Dict, List, Optional, Tuple

import requests
from sqlmodel import Session, select, update

from app.config import settings
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_contacts import SequenceCampaignContacts, StatusEnum
from app.models.sequence.linkedin_account import LinkedInAccount

unipile_dsn = settings.UNIPILE_DSN
unipile_api_key = settings.UNIPILE_APIKEY


def extract_vanity_name_linkedin(linkedin_url):
    if not linkedin_url:
        return None
    pattern = r"(?<=linkedin.com/in/)[^/]+"
    match = re.search(pattern, linkedin_url)
    if match:
        return match.group(0)
    else:
        return None


def retrieve_users(user_identifier: str, account_id: str, notify=False):
    url = (
        f"https://{unipile_dsn}/api/v1/users/{user_identifier}?account_id={account_id}"
    )
    if notify:
        url += "&notify=true"
    headers = {
        "accept": "application/json",
        "X-API-KEY": unipile_api_key,
    }

    response = requests.get(url, headers=headers)
    # if response.status_code == 200:
    #     return response.json()
    # else:
    #     return None
    try:
        return response.json()
    except ValueError:
        return None


def send_message(
    payload: Dict[str, Any],
    files: Optional[List[Tuple[str, Tuple[str, bytes, str]]]] = None,
    is_inmail: Optional[bool] = False,
):
    url = f"https://{unipile_dsn}/api/v1/chats"
    if is_inmail:
        payload["linkedin[inmail]"] = "true"
        payload["linkedin[api]"] = "classic"
    headers = {
        "accept": "application/json",
        "X-API-KEY": unipile_api_key,
    }
    response = requests.post(url=url, data=payload, headers=headers, files=files)
    try:
        data = response.json()
    except ValueError:
        data = {"raw": response.text}

    return response.ok, data


def send_invitation(provider_id: str, account_id: str, message: Optional[str] = None):
    url = f"https://{unipile_dsn}/api/v1/users/invite"
    payload = {
        "provider_id": provider_id,
        "account_id": account_id,
    }
    if message:
        payload["message"] = message
    headers = {
        "accept": "application/json",
        "X-API-KEY": unipile_api_key,
    }
    response = requests.post(url, json=payload, headers=headers)
    try:
        data = response.json()
    except ValueError:
        data = {"raw": response.text}

    return response.ok, data


def restart(db: Session, account_id: str):
    url = f"https://{unipile_dsn}/api/v1/accounts/{account_id}/restart"

    headers = {
        "accept": "application/json",
        "X-API-KEY": unipile_api_key,
    }

    response = requests.post(url, headers=headers)

    if response.ok:
        return True
    else:
        account = db.exec(
            select(LinkedInAccount).where(
                LinkedInAccount.account_id == account_id,
                LinkedInAccount.deleted_at.is_(None),
                LinkedInAccount.account_type == "LINKEDIN",
            )
        ).first()

        if account.is_default:
            team_id = account.team_id
            db.execute(
                update(SequenceCampaignContacts)
                .where(
                    SequenceCampaignContacts.sequence_campaign_id.in_(
                        select(SequenceCampaign.id).where(
                            SequenceCampaign.team_id == team_id,
                            SequenceCampaign.deleted_at.is_(None),
                        )
                    ),
                    SequenceCampaignContacts.deleted_at.is_(None),
                    SequenceCampaignContacts.status == StatusEnum.PAUSE.value,
                )
                .values(status=StatusEnum.ACTIVE.value)
            )
            db.commit()

        return False
