output "data_collection_bucket_name" {
  value = module.data_collection_bucket.bucket_id
  description = "Name of the Data Collection Bucket"
}

output "athena_query_results_bucket_name" {
  value = module.athena_query_results_bucket.bucket_id
  description = "Name of the Athena Query Results Bucket"
}

output "function_arn" {
  value = module.lambda.function_arn
  description = "ARN of the Lambda function"
}

output "quicksight_datasource_role_arn" {
  value = aws_iam_role.qs_role.arn
  description = "ARN of the IAM Role used by QuickSight datasources"
}

output "athena_workgroup_name" {
  value = var.athena_workgroup_name
  description = "Name of the Athena Workgroup"
}

output "athena_database_name" {
  value = var.athena_database_name
  description = "Name of the Athena database"
}