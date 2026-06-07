#!/bin/bash
echo "Initializing LocalStack S3 buckets..."
awslocal s3 mb s3://kgpone-assets
awslocal s3api put-bucket-cors --bucket kgpone-assets --cors-configuration '{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag"]
    }
  ]
}'
echo "LocalStack S3 initialized."
