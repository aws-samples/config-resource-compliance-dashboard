variable "region" {
    type = string
    description = "AWS region where we're deploying"
    default = "eu-west-1"
}

variable "logging_bucket_prefix" {
    type = string
    description = "Prefix of the bucket used for logging"
    default = "configlogging"
}

variable "data_collection_bucket_prefix" {
    type = string
    description = "Prefix of bucket used to store AWS Config Configuration Snapshots and AWS CloudTrail events"
    default = "configdata"
}

variable "athena_query_results_bucket_prefix" {
    type = string
    description = "Prefix of bucket used to store the Athena Query results"
    default = "configathenaresults"
}

variable "function_name" {
    type = string
    description = "Name of the Lambda function"
    default = "lambda-cid-config"
}

variable "cloudwatch_policy_name" {
    type = string
    description = "Name of the CloudWatch policy of the Lambda function"
    default = "lambda-cid-config-cloudwatch-policy"
}

variable "s3_policy_name" {
    type = string
    description = "Name of the S3 policy of the Lambda function"
    default = "lambda-cid-config-s3-policy"
}

variable "athena_policy_name" {
    type = string
    description = "Name of the Athena policy of the Lambda function"
    default = "lambda-cid-config-athena-policy"
}

variable "glue_policy_name" {
    type = string
    description = "Name of the Glue policy of the Lambda function"
    default = "lambda-cid-config-glue-policy"
}

variable "athena_workgroup_name" {
    type = string
    description = "Name of the Athena WorkGroup"
    default = "cid-config-athena-workgroup"
}

variable "athena_database_name" {
    type = string
    description = "Name of the Athena database"
    default = "cid_config_athena_database"
}

variable "athena_config_table_name" {
    type = string
    description = "Name of the Athena table for AWS Config data"
    default = "aws_config_configuration_snapshots"
}

variable "athena_cloudtrail_table_name" {
    type = string
    description = "Name of the Athena table for CloudTrail data"
    default = "aws_cloudtrail_events"
}