output "bucket_regional_domain_name" {
    description = "S3 bucket regional domain name"
    value = aws_s3_bucket.s3_bucket.bucket_regional_domain_name
}

output "bucket_id" {
    description = "ID of the S3 bucket"
    value = aws_s3_bucket.s3_bucket.id
}

output "bucket_arn" {
    description = "ARN of the S3 bucket"
    value = aws_s3_bucket.s3_bucket.arn
}