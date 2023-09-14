variable "region" {
    type = string
    description = "AWS region where we're deploying"
    default = "eu-west-1"
}

variable "replication_role_name" {
    type = string
    description = "Name of the IAM role needed for replication"
    default = "crcd_replication_role"
}

variable "source_bucket_name" {
    type = string
    description = "Name of the source S3 bucket to replicate"
    default = ""
}

variable "destination_bucket_name" {
    type = string
    description = "Name of the source S3 bucket to replicate"
    default = ""
}