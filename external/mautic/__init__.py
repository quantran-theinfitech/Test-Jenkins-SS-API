import json
import uuid
from typing import List

import requests
from requests.auth import HTTPBasicAuth

from app.config import settings
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.contact import SequenceContact
from app.models.sequence.step import SequenceCampaignStep
from external.mautic.request import (
    default_mautic_campaign_request,
    make_mautic_campaign_request,
    make_mautic_contacts_request,
    make_mautic_mail_request,
)
from external.mautic.schema.campaign import (
    MauticCampaign,
    MauticCampaignResponse,
    MauticEditCampaignInput,
    MauticSegmentResponse,
)
from external.mautic.schema.mail_template import (
    MauticMailTemplate,
    MauticMailTemplateResponse,
)
from external.mautic.schema.person import MauticBatchPersonResponse, PersonOutput


def logging_decorator(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Finished {func.__name__}")
        return result

    return wrapper


class LoggingDecorator:
    @classmethod
    def exclude_logging(cls):
        return []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        exclude = cls.exclude_logging()
        for attr, value in cls.__dict__.items():
            if callable(value) and attr not in exclude:
                setattr(cls, attr, logging_decorator(value))


class MauticService(LoggingDecorator):
    @classmethod
    def exclude_logging(cls):
        return [
            "make_post_request",
            "__init__",
            "make_patch_request",
            "make_put_request",
        ]

    def __init__(self):
        self.base_url = settings.MAUTIC_BASE_URL.strip("/")
        self.auth = HTTPBasicAuth(settings.MAUTIC_USERNAME, settings.MAUTIC_PASSWORD)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def create_campaign(
        self, campaign: SequenceCampaign, mautic_segment_id: int
    ) -> MauticCampaign:
        request = default_mautic_campaign_request(campaign, mautic_segment_id)

        resp = self.make_post_request(
            f"{self.base_url}/api/campaigns/new",
            request.json(exclude_none=True),
        )

        mautic_campaign = MauticCampaignResponse(**resp)

        return mautic_campaign.campaign

    def edit_campaign(
        self,
        campaign: SequenceCampaign,
        mautic_campaign_id: int,
        mautic_segment_id: int,
        data: List[MauticEditCampaignInput],
    ) -> MauticCampaign:
        request = make_mautic_campaign_request(campaign, mautic_segment_id, data)

        resp = self.make_put_request(
            f"{self.base_url}/api/campaigns/{mautic_campaign_id}/edit",
            request.json(exclude_none=True),
        )

        mautic_campaign = MauticCampaignResponse(**resp)

        return mautic_campaign.campaign

    def create_contacts(self, contacts: List[SequenceContact]) -> List[PersonOutput]:
        payload = make_mautic_contacts_request(contacts)
        resp = self.make_post_request(
            f"{self.base_url}/api/contacts/batch/new",
            json.dumps(payload),
        )

        mautic_contacts = MauticBatchPersonResponse(**resp)

        output = []
        for contact in mautic_contacts.contacts:
            uuid = contact.fields.all.email.split("@")[0]
            output.append(
                PersonOutput(
                    mautic_contact_id=contact.id,
                    uuid=uuid,
                )
            )

        return output

    def delete_contact(self, mautic_contact_id: int):
        self.make_delete_request(
            f"{self.base_url}/api/contacts/{mautic_contact_id}/delete"
        )

    def create_segment(self) -> int:
        payload = {
            "name": uuid.uuid4().hex,
            "description": "Created from salessmart",
            "isPublished": True,
            "isGlobal": False,
        }
        segment = self.make_post_request(
            f"{self.base_url}/api/segments/new", json.dumps(payload)
        )

        segment = MauticSegmentResponse(**segment)

        return segment.list.id

    def add_contact_to_segment(
        self, mautic_contact_ids: List[int], mautic_segment_id: int
    ):
        payload = {
            "ids": mautic_contact_ids,
        }
        self.make_post_request(
            f"{self.base_url}/api/segments/{mautic_segment_id}/contacts/add",
            json.dumps(payload),
        )

    def create_email_template(self, subject: str, content: str) -> MauticMailTemplate:
        request = make_mautic_mail_request(subject, content)
        resp = self.make_post_request(
            f"{self.base_url}/api/emails/new",
            request.json(exclude_none=True),
        )

        mautic_template = MauticMailTemplateResponse(**resp)

        return mautic_template.email

    def edit_email_template(
        self, mautic_template_id: int, subject: str, content: str
    ) -> MauticMailTemplate:
        request = make_mautic_mail_request(subject, content)
        resp = self.make_patch_request(
            f"{self.base_url}/api/emails/{mautic_template_id}/edit",
            request.json(exclude_none=True),
        )

        mautic_template = MauticMailTemplateResponse(**resp)

        return mautic_template.email

    def make_delete_request(self, url):
        try:
            resp = requests.delete(
                headers=self.headers,
                url=url,
                auth=self.auth,
            )
            return resp.json()
        except Exception as e:
            print(e)
            return None

    def make_post_request(self, url, payload):
        try:
            resp = requests.post(
                headers=self.headers,
                url=url,
                data=payload,
                auth=self.auth,
                verify=settings.MAUTIC_VERIFY_SSL,
            )
            return resp.json()
        except Exception as e:
            print(e)
            return None

    def make_patch_request(self, url, payload):
        try:
            resp = requests.patch(
                headers=self.headers,
                url=url,
                data=payload,
                auth=self.auth,
                verify=settings.MAUTIC_VERIFY_SSL,
            )
            return resp.json()
        except Exception as e:
            print(e)
            return None

    def make_put_request(self, url, payload):
        try:
            resp = requests.put(
                headers=self.headers,
                url=url,
                data=payload,
                auth=self.auth,
                verify=settings.MAUTIC_VERIFY_SSL,
            )
            return resp.json()
        except Exception as e:
            print(e)
            return None
