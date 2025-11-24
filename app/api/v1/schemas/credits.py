from pydantic import BaseModel


class CreditsStatusResponse(BaseModel):
    amount: int
    used_amount: int
    service_code: str
