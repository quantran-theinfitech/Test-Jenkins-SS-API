import boto3
from botocore.exceptions import ClientError

from app.config import settings


class S3Service:
    def __init__(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        self.s3_client = self.get_s3_client()

    def get_s3_client(self):
        return boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_SERVER_PUBLIC_KEY,
            aws_secret_access_key=settings.AWS_SERVER_SECRET_KEY,
            region_name=settings.AWS_REGION_NAME,
        )

    def generate_presigned_url(self, object_name: str, expiration=3600):
        try:
            response_url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": object_name,
                },
                ExpiresIn=expiration,
            )
            return response_url
        except ClientError as e:
            print(e)
            return None

    def generate_presigned_upload_url(self, object_name: str, expiration=3600):
        try:
            response_url = self.s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": object_name,
                },
                ExpiresIn=expiration,
            )
            return response_url
        except ClientError as e:
            print(e)
            return None

    def upload_file(self, file_path: str, object_name: str = None):
        """
        Upload a file to an S3 bucket.

        :param file_path: Path to the file to upload.
        :param object_name: S3 object name. If not specified, file_path is used.
        :return: True if file was uploaded, else False.
        """
        if object_name is None:
            object_name = file_path

        try:
            self.s3_client.upload_file(file_path, self.bucket_name, object_name)
            print(f"File {file_path} uploaded to {self.bucket_name}/{object_name}")
            return True
        except ClientError as e:
            print(f"Failed to upload file {file_path} to S3: {e}")
            return False

    def put_object(
        self, object_name: str, content: str, content_type: str = "text/plain"
    ):
        """
        Upload content directly to S3 as an object.

        :param object_name: The name of the object in the S3 bucket.
        :param content: The content to upload.
        :param content_type: The MIME type of the content (default is "text/plain").
        :return: True if the object was uploaded successfully, else False.
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=content,
                ContentType=content_type,
            )
            print(f"Object {object_name} uploaded to bucket {self.bucket_name}")
            return True
        except ClientError as e:
            print(f"Failed to upload object {object_name} to S3: {e}")
            return False

    def get_object(self, object_name: str):
        """
        Retrieve an object from S3.

        :param object_name: The name of the object in the S3 bucket.
        :return: The content of the object as a string, or None if retrieval fails.
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=object_name
            )
            content = response["Body"]
            print(
                f"Object {object_name} retrieved successfully from bucket {self.bucket_name}"
            )
            return content
        except ClientError as e:
            print(f"Failed to retrieve object {object_name} from S3: {e}")
            return None

    def get_object_bytes(self, object_name: str):
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=object_name
            )
            # The streaming body needs to be read to obtain bytes
            content_bytes: bytes = response["Body"].read()
            file_type = response["ContentType"]
            print(
                f"Object {object_name} retrieved successfully from bucket {self.bucket_name} (bytes length={len(content_bytes)})"
            )
            return content_bytes, file_type
        except ClientError as e:
            print(f"Failed to retrieve object {object_name} from S3: {e}")
            return None

    def move_file_from_tmp(self, presigned_key: str):
        try:
            if not presigned_key:
                return presigned_key
            if not presigned_key.startswith(settings.MEDIA_PATH_TMP_PREFIX):
                return presigned_key
            destination_key = presigned_key[len(settings.MEDIA_PATH_TMP_PREFIX) :]
            copy_source = {"Bucket": self.bucket_name, "Key": presigned_key}
            self.s3_client.copy_object(
                CopySource=copy_source, Bucket=self.bucket_name, Key=destination_key
            )
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=presigned_key)
            return destination_key
        except ClientError as e:
            print(f"Error with S3 move_file_from_tmp: {str(e)}")
            return presigned_key

    def get_object_metadata(self, object_name: str):
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name, Key=object_name
            )
            return response
        except ClientError as e:
            print(f"Failed to retrieve metadata {object_name} from S3: {e}")
            return None

    def generate_presigned_url_from_s3_uri(self, s3_uri: str, expiration=3600):
        """
        Convert s3://bucket/key to a presigned url
        """
        if not s3_uri.startswith("s3://"):
            return s3_uri  # nếu đã là http rồi thì trả về luôn

        # cắt bucket và key từ s3_uri
        parts = s3_uri.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]

        # nếu bucket trong uri khác bucket config -> dùng bucket trong uri
        bucket_to_use = bucket if bucket else self.bucket_name

        try:
            response_url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": bucket_to_use,
                    "Key": key,
                    "ResponseContentDisposition": "inline",
                    "ResponseContentType": "application/pdf",
                },
                ExpiresIn=expiration,
            )
            return response_url
        except ClientError as e:
            print(f"Error generating presigned url from {s3_uri}: {e}")
            return None

    def download_file(self, s3_uri: str):
        if not s3_uri.startswith("s3://"):
            return s3_uri  # nếu đã là http rồi thì trả về luôn

        # cắt bucket và key từ s3_uri
        parts = s3_uri.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]

        # nếu bucket trong uri khác bucket config -> dùng bucket trong uri
        bucket_to_use = bucket if bucket else self.bucket_name

        try:
            response_url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": bucket_to_use,
                    "Key": key,
                },
            )
            return response_url
        except ClientError as e:
            print(f"Error generating presigned url from {s3_uri}: {e}")
            return None
