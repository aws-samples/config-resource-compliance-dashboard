data aws_caller_identity current {}

# Get bucket ARNs

data "aws_s3_bucket" "data_source_bucket" {
  bucket = var.data_collection_bucket_name
}

# IAM role for Lambda function

data "aws_iam_policy_document" "lambda_athena_policy_document" {

  statement {
    sid    = "AthenaAccess"
    effect = "Allow"
    actions = [
        "athena:StartQueryExecution",
        "athena:GetQueryExecution"
    ]
    resources = ["arn:aws:athena:${var.region}:${data.aws_caller_identity.current.account_id}:workgroup/${var.athena_workgroup_name}"]
  }
}

resource "aws_iam_policy" "lambda_athena_policy" {
  name_prefix = "athena-${var.athena_policy_name}"
  description = "Policy that gives Athena permissisons to Lambda IAM role"
  policy      = data.aws_iam_policy_document.lambda_athena_policy_document.json
}

data "aws_iam_policy_document" "lambda_glue_policy_document" {

  statement {
    sid    = "Glue"
    effect = "Allow"
    actions = [
        "glue:GetTable",
        "glue:GetTables",
        "glue:BatchCreatePartition",
        "glue:CreatePartition",
        "glue:DeletePartition",
        "glue:BatchDeletePartition",
        "glue:UpdatePartition",
        "glue:GetPartition",
        "glue:GetPartitions",
        "glue:BatchGetPartition"
    ]
    resources = [
        "arn:aws:glue:${var.region}:${data.aws_caller_identity.current.account_id}:table/${var.athena_database_name}/*",
        "arn:aws:glue:${var.region}:${data.aws_caller_identity.current.account_id}:catalog",
        "arn:aws:glue:${var.region}:${data.aws_caller_identity.current.account_id}:database/${var.athena_database_name}"
    ]
  }
}

resource "aws_iam_policy" "lambda_glue_policy" {
  name_prefix = "glue-${var.glue_policy_name}"
  description = "Policy that gives Glue permissisons to Lambda IAM role"
  policy      = data.aws_iam_policy_document.lambda_glue_policy_document.json
}

data "aws_iam_policy_document" "lambda_cloudwatch_policy_document" {

  statement {
    sid    = "CloudWatchLogGroup"
    effect = "Allow"
    actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.function_name}:*"]
  }
}

resource "aws_iam_policy" "lambda_cloudwatch_policy" {
  name_prefix = "cloudwatch-logs-${var.cloudwatch_policy_name}"
  description = "Policy that gives CloudWatch Logs permissisons to Lambda IAM role"
  policy      = data.aws_iam_policy_document.lambda_cloudwatch_policy_document.json
}

data "aws_iam_policy_document" "lambda_s3_policy_document" {

  statement {
    sid    = "S3"
    effect = "Allow"
    actions = [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:GetBucketLocation",
        "s3:ListMultipartUploadParts",
        "s3:PutObject"
    ]
    resources = ["${var.athena_query_results_bucket_arn}", "${var.athena_query_results_bucket_arn}/*"]
  }
}

resource "aws_iam_policy" "lambda_s3_policy" {
  name_prefix = "s3-${var.s3_policy_name}"
  description = "Policy that gives S3 permissisons to Lambda IAM role"
  policy      = data.aws_iam_policy_document.lambda_s3_policy_document.json
}

resource "aws_iam_role" "lambda_role" {
  name = "${var.function_name}"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_cloudwatch_policy_attachment" {
  policy_arn = aws_iam_policy.lambda_cloudwatch_policy.arn
  role       = aws_iam_role.lambda_role.name
}

resource "aws_iam_role_policy_attachment" "lambda_s3_policy_attachment" {
  policy_arn = aws_iam_policy.lambda_s3_policy.arn
  role       = aws_iam_role.lambda_role.name
}

resource "aws_iam_role_policy_attachment" "lambda_config_athena_policy_attachment" {
  policy_arn = aws_iam_policy.lambda_athena_policy.arn
  role       = aws_iam_role.lambda_role.name
}

resource "aws_iam_role_policy_attachment" "lambda_config_glue_policy_attachment" {
  policy_arn = aws_iam_policy.lambda_glue_policy.arn
  role       = aws_iam_role.lambda_role.name
}

# Lambda function

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir = "../source/data_collection_lambda_compliance/"
  output_path = "../source/data_collection_lambda_compliance.zip"
}

resource "aws_lambda_function" "data_collection_lambda_compliance" {

  #checkov:skip=CKV_AWS_116: "Ensure that AWS Lambda function is configured for a Dead Letter Queue(DLQ)" - Not required, since it adds unnecessary complexity to the solution
  #checkov:skip=CKV_AWS_173: "Check encryption settings for Lambda environmental variable" - Using AWS Managed Key to encrypt environment variables
  #checkov:skip=CKV_AWS_272: "Ensure AWS Lambda function is configured to validate code-signing" - Not required, since it adds unnecessary complexity to the solution and dependencies with AWS Signer

  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  filename      = "../source/data_collection_lambda_compliance.zip"
  function_name = "${var.function_name}"
  role = aws_iam_role.lambda_role.arn
  description = "Lambda function that adds partitions when there are new Configuration Snapshots or CloudTrail events"
  handler = "lambda_function.lambda_handler"
  runtime = "python3.10"
  memory_size = 128
  timeout = 300
  reserved_concurrent_executions = 1

  tracing_config {
    mode = "Active"
  }

  # nosemgrep: ruleid: aws-lambda-environment-unencrypted
  environment { 
    variables = {
      ATHENA_QUERY_RESULTS_BUCKET_NAME = var.athena_query_results_bucket_name,
      CLOUDTRAIL_TABLE_NAME = var.athena_cloudtrail_table_name,
      CONFIG_TABLE_NAME = var.athena_config_table_name,
      DATABASE_NAME = var.athena_database_name,
      REGION = var.region,
      WORKGROUP = var.athena_workgroup_name
    }
  }

    vpc_config {
      subnet_ids         = var.subnet_ids
      security_group_ids = var.security_group_ids
    }

}

# Notification triggers for Lambda

resource "aws_lambda_permission" "lambda_permission" {
  
  statement_id  = "AllowS3BucketToTriggerLambda"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_collection_lambda_compliance.arn
  principal     = "s3.amazonaws.com"
  source_account = data.aws_caller_identity.current.account_id
  source_arn    = data.aws_s3_bucket.data_source_bucket.arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  
  bucket = var.data_collection_bucket_name

  lambda_function {
    lambda_function_arn = aws_lambda_function.data_collection_lambda_compliance.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "AWSLogs/"
  }

  depends_on = [aws_lambda_permission.lambda_permission]
}