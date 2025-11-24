from typing import List, Optional

from pydantic import BaseModel

# Key: mautic field
# Value: SS sequence person field
SS_FIELD_MAPPING = {
    "sequence_email": "email",
    "firstname": "name",
    "email": "uuid",
    # "lastname": "last_name",
}


class PersonOutput(BaseModel):
    mautic_contact_id: int
    uuid: str


class MauticField(BaseModel):
    id: Optional[int]
    sequence_email: Optional[str]
    email: Optional[str]
    firstname: Optional[str]


class MauticPersonField(BaseModel):
    all: MauticField


class MauticPerson(BaseModel):
    id: int
    email: Optional[str]
    fields: MauticPersonField


class MauticPersonRequest(MauticField):
    pass


class MauticBatchPersonResponse(BaseModel):
    contacts: List[MauticPerson]
