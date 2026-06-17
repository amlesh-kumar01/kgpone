import logging
from src.utils.interfaces import IS3Storage
from src.infrastructure.s3 import get_s3_client
from src.config.settings import Settings

logger = logging.getLogger("s3_repository")

class S3Storage(IS3Storage):
    def __init__(self):
        self.bucket_name = Settings.S3_BUCKET_NAME

    def upload(self, file_name: str, file_content: bytes):
        """Uploads a file directly to the S3 bucket."""
        client = get_s3_client()
        if client is None:
            raise RuntimeError("S3 client is not initialized.")
        client.put_object(
            Bucket=self.bucket_name,
            Key=file_name,
            Body=file_content
        )

    def download_file(self, file_key: str, download_path: str):
        """Downloads a file from S3 to the local filesystem."""
        client = get_s3_client()
        if client is None:
            raise RuntimeError("S3 client is not initialized.")
        client.download_file(
            Bucket=self.bucket_name,
            Key=file_key,
            Filename=download_path
        )

    def generate_presigned_url(self, file_key: str, content_type: str, expiration: int = 3600) -> dict:
        """Generates a presigned URL for direct upload."""
        client = get_s3_client()
        if client is None:
            raise RuntimeError("S3 client is not initialized.")
        url = client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": file_key,
                "ContentType": content_type
            },
            ExpiresIn=expiration
        )
        return {"upload_url": url, "file_key": file_key}
