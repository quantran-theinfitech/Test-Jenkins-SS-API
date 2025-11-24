from enum import Enum
from typing import Optional

from pydantic import BaseModel


class TemplateEmailType(Enum):
    LIST = "list"
    TEMPLATE = "template"


class Template(Enum):
    MAUTIC_CODE_MODE = "mautic_code_mode"


class MauticMailTemplate(BaseModel):
    id: Optional[int] = None
    subject: str
    emailType: TemplateEmailType
    template: Template
    plainText: Optional[str]
    customHtml: Optional[str]
    name: str
    isPublished: bool


class MauticMailTemplateResponse(BaseModel):
    email: MauticMailTemplate
