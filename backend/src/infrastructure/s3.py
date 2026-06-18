import logging
import boto3
from botocore.config import Config
from src.config.settings import Settings

logger = logging.getLogger("s3_config")

_s3_client = None

def get_s3_client():
    """Initializes and returns the boto3 S3 client singleton."""
    global _s3_client
    if _s3_client is None:
        try:
            session_kwargs = {}
            if Settings.AWS_ACCESS_KEY_ID:
                session_kwargs["aws_access_key_id"] = Settings.AWS_ACCESS_KEY_ID
            if Settings.AWS_SECRET_ACCESS_KEY:
                session_kwargs["aws_secret_access_key"] = Settings.AWS_SECRET_ACCESS_KEY

            client_kwargs = {
                "region_name": Settings.AWS_DEFAULT_REGION
            }
            if Settings.S3_ENDPOINT_URL and Settings.S3_ENDPOINT_URL.startswith(("http://", "https://")):
                client_kwargs["endpoint_url"] = Settings.S3_ENDPOINT_URL

            # Enable modern S3 signature support (avoids signature version issues)
            client_kwargs["config"] = Config(signature_version="s3v4")

            _s3_client = boto3.client("s3", **session_kwargs, **client_kwargs)
            logger.info("Successfully initialized S3 boto3 client")
        except Exception as e:
            logger.error(f"Failed to initialize S3 boto3 client: {e}")
            _s3_client = None
    return _s3_client
