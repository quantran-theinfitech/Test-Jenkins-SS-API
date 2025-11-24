from typing import List, Optional

from pydantic import BaseModel


class FillFormRequest(BaseModel):
    html: str


class FillFormItem(BaseModel):
    xpath: str
    key_name: str


class FillFormResponse(BaseModel):
    fill_form: Optional[List[FillFormItem]] = None
