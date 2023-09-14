variable "data_collection_bucket_name" {
    type = string
    description = "Name of the Data Collection Bucket"
}

variable "iam_role_arn" {
    type = string
    description = "ARN of the IAM Role used by AWS Config"
}