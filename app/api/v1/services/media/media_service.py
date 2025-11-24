from external.s3 import S3Service

s3_service = S3Service()


def generate_presigned_upload_url(object_name: str):
    return s3_service.generate_presigned_upload_url(object_name)


def get_presigned_url(presigned_key: str):
    if not presigned_key:
        return None
    return s3_service.generate_presigned_url(presigned_key)


def move_file_from_tmp_to_perm(presigned_key: str):
    return s3_service.move_file_from_tmp(presigned_key)
