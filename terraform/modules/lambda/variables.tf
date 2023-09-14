variable "region" {
    type = string
    description = "AWS region where we're deploying"
}

variable "function_name" {
    type = string
    description = "Name with suffix of the Lambda function"
}

variable "cloudwatch_policy_name" {
    type = string
    description = "Name of the policy to give Lambda access to CloudWatch Logs"
}

variable "s3_policy_name" {
    type = string
    description = "Name of the policy to give Lambda access to S3"
}

variable "athena_policy_name" {
    type = string
    description = "Name of the policy to give Lambda access to Athena"
}

variable "glue_policy_name" {
    type = string
    description = "Name of the policy to give Lambda access to Glue"
}

variable "athena_config_table_name" {
    type = string
    description = "Name of the Athena table where the Lambda will add partitions containing AWS Config logs"
}

variable "athena_cloudtrail_table_name" {
    type = string
    description = "Name of the Athena table where the Lambda will add partitions containing Amazon CloudTrail logs"
}

variable "athena_database_name" {
    type = string
    description = "Name of the Athena database where the Lambda will add partitions containing AWS Config logs"
}

variable "athena_workgroup_name" {
    type = string
    description = "Name of the Athena workgroup"
}

variable "athena_query_results_bucket_name" {
    type = string
    description = "Name of bucket used to store the Athena Query results"
}

variable "athena_query_results_bucket_arn" {
    type = string
    description = "ARN of bucket used to store the Athena Query results"
}

variable "data_collection_bucket_name" {
    type = string
    description = "Name of bucket used to store the AWS Config Snapshots and AWS CloudTrail events"
}
variable "subnet_ids" {
  type        = list(string)
  default     = []
  description = "List of subnet IDs to which the Lambda function should be attached"
}

variable "security_group_ids" {
  type        = list(string)
  default     = []
  description = "List of security group IDs to which the Lambda function should be attached"
}
