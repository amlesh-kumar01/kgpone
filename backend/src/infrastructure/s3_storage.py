import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class S3Storage:
    def __init__(self):
        # We assume credentials and region are loaded via environment variables 
        # (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION)
        endpoint_url = os.getenv('AWS_ENDPOINT_URL') or os.getenv('S3_ENDPOINT_URL')
        if endpoint_url:
            self.s3_client = boto3.client('s3', endpoint_url=endpoint_url)
        else:
            self.s3_client = boto3.client('s3')
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'kgpone-course-materials')

    def generate_presigned_url(self, file_key: str, content_type: str, expiration: int = 900) -> Dict[str, Any]:
        """
        Generate a presigned URL to allow the frontend to PUT a file directly to S3.
        expiration is in seconds (900 = 15 minutes)
        """
        try:
            response = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key,
                    'ContentType': content_type
                },
                ExpiresIn=expiration
            )
            return {
                "upload_url": response,
                "file_key": file_key
            }
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            raise
