resource "aws_s3_bucket_logging" "s3_bucket" {

  bucket = var.bucket_name

  target_bucket = var.logging_bucket_name
  target_prefix = "log/"
}