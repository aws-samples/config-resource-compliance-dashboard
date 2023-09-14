output "replication_role_arn" {
    value = aws_iam_role.replication_role.arn
    description = "ARN of the IAM role needed for replication"
}

output "destination_bucket_arn" {
    value = "arn:aws:s3:::${var.destination_bucket_name}"
    description = "ARN of the Data Collection Bucket"
}