import logging
from src.utils.interfaces import IS3Storage
from src.infrastructure.s3 import get_s3_client
from src.config.settings import Settings

logger = logging.getLogger("s3_repository")

class S3Storage(IS3Storage):
    def __init__(self):
        self.bucket_name = Settings.S3_BUCKET_NAME

    def upload(self, file_key: str, file_content: bytes):
        """Uploads a file directly to the S3 bucket."""
        client = get_s3_client()
        if client is None:
            raise RuntimeError("S3 client is not initialized.")
        client.put_object(
            Bucket=self.bucket_name,
            Key=file_key,
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

    def generate_presigned_url(self, file_key: str, content_type: str = None, expiration: int = 3600, action: str = "put_object") -> dict:
        """Generates a presigned URL for direct upload or download."""
        client = get_s3_client()
        if client is None:
            raise RuntimeError("S3 client is not initialized.")
            
        params = {
            "Bucket": self.bucket_name,
            "Key": file_key
        }
        if content_type and action == "put_object":
            params["ContentType"] = content_type
            
        url = client.generate_presigned_url(
            ClientMethod=action,
            Params=params,
            ExpiresIn=expiration
        )
        return {"url": url, "file_key": file_key}

    def delete_file(self, file_key: str):
        client = get_s3_client()
        if client is None:
            raise RuntimeError("S3 client is not initialized.")
        try:
            client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
        except Exception as e:
            # Idempotent: Ignore errors when deleting missing files
            logger.warning(f"S3 deletion error for {file_key}: {e}")
            pass
