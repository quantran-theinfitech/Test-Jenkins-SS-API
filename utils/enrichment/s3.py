import uuid
from datetime import datetime

from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile

from external.s3 import S3Service

OBJECT_NAME_PREFIX = "enrichment_files"


def save_file_to_s3(file: UploadFile, enrichment_id: int):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"{str(uuid.uuid4())}_{timestamp}.csv"
    s3_service = S3Service()
    try:
        file.file.seek(0)
        file_content = file.file.read()

        if not file_content or len(file_content) == 0:
            print("File content is empty!")
            raise HTTPException(status_code=400, detail="File is empty")

        object = s3_service.put_object(
            f"{OBJECT_NAME_PREFIX}/{enrichment_id}/{file_name}",
            file_content,
            content_type="text/csv",
        )
        if not object:
            raise HTTPException(status_code=500, detail="common.uploadFileFailed")
    except (Exception, ClientError) as e:
        print(f"Failed to save file to S3: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file to S3")
    return file_name


def get_file_from_s3(enrichment_id: int, object_key: str):
    s3_service = S3Service()
    result = s3_service.get_object_bytes(
        f"{OBJECT_NAME_PREFIX}/{enrichment_id}/{object_key}"
    )
    if result:
        content_bytes, file_type = result
        return content_bytes
    return None
