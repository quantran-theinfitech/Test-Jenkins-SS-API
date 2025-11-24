from pydantic import BaseModel


class PresignedUploadUrlResponse(BaseModel):
    upload_url: str
    get_url: str
    path: str


class PresignedUrlResponse(BaseModel):
    url: str
