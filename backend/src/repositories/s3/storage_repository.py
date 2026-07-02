import logging
from src.utils.interfaces import IS3Storage
from src.infrastructure.s3 import get_s3_client
from src.config.settings import Settings

logger = logging.getLogger("s3_repository")

class S3Storage(IS3Storage):
    def __init__(self):
        self.bucket_name = Settings.S3_BUCKET_NAME

    def upload(self, file_key: str, file_content: bytes, content_type: str = "application/octet-stream"):
        """Uploads a file directly to the S3 bucket."""
        client = get_s3_client()
        if client is None:
            raise RuntimeError("S3 client is not initialized.")
        client.put_object(
            Bucket=self.bucket_name,
            Key=file_key,
            Body=file_content,
            ContentType=content_type,
        )

    def upload_image(self, file_key: str, image_bytes: bytes, content_type: str = "image/png") -> str:
        """Uploads an image to S3 and returns the s3_key."""
        self.upload(file_key, image_bytes, content_type=content_type)
        return file_key

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

    def generate_presigned_get_url(self, file_key: str, expiration: int = 3600) -> str:
        """Generates a presigned GET URL for reading a file (e.g. an image)."""
        client = get_s3_client()
        if client is None:
            raise RuntimeError("S3 client is not initialized.")
        return client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self.bucket_name, "Key": file_key},
            ExpiresIn=expiration,
        )

    def list_and_delete_prefix(self, prefix: str) -> int:
        """
        Deletes all S3 objects under the given prefix (e.g. 'images/{doc_id}/').
        Returns the number of objects deleted.
        """
        client = get_s3_client()
        if client is None:
            raise RuntimeError("S3 client is not initialized.")

        deleted_count = 0
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            objects = page.get("Contents", [])
            if not objects:
                continue
            delete_payload = {"Objects": [{"Key": obj["Key"]} for obj in objects]}
            try:
                response = client.delete_objects(
                    Bucket=self.bucket_name, Delete=delete_payload
                )
                deleted_count += len(response.get("Deleted", []))
            except Exception as e:
                logger.warning(f"Batch delete error for prefix '{prefix}': {e}")

        logger.info(f"Deleted {deleted_count} objects under prefix '{prefix}'")
        return deleted_count

