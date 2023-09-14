output "function_arn" {
  value = aws_lambda_function.data_collection_lambda_compliance.arn
  description = "ARN of the Lambda function"
}