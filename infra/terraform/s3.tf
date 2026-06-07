resource "aws_s3_bucket" "knowledgeos_bucket" {
  bucket = var.s3_bucket_name
}

resource "aws_s3_bucket_cors_configuration" "knowledgeos_bucket_cors" {
  bucket = aws_s3_bucket.knowledgeos_bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "POST", "GET"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}
