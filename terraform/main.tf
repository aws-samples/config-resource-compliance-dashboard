data "aws_caller_identity" "current" {}

# S3 buckets

module "logging_bucket" {

    source = "./modules/s3"
    bucket_name = "${var.logging_bucket_prefix}${data.aws_caller_identity.current.account_id}"
}

module "data_collection_bucket" {

    source = "./modules/s3"
    bucket_name = "${var.data_collection_bucket_prefix}${data.aws_caller_identity.current.account_id}"
}

module "athena_query_results_bucket" {

    source = "./modules/s3"
    bucket_name = "${var.athena_query_results_bucket_prefix}${data.aws_caller_identity.current.account_id}"
}

# Enable S3 logging for buckets that are not the logging bucket

module "data_collection_bucket_logging" {

    source = "./modules/s3_logging"
    bucket_name = module.data_collection_bucket.bucket_id
    logging_bucket_name = module.logging_bucket.bucket_id
}

module "athena_query_results_bucket_logging" {

    source = "./modules/s3_logging"
    bucket_name = module.athena_query_results_bucket.bucket_id
    logging_bucket_name = module.logging_bucket.bucket_id
}

# Enable versioning data collection bucket

resource "aws_s3_bucket_versioning" "data_collection_bucket_versioning" {
  bucket = module.data_collection_bucket.bucket_id
  versioning_configuration {
    status = "Enabled"
  }
}

# Athena workgroup

module "athena" {
    source = "./modules/athena"
    athena_query_results_bucket_name = module.athena_query_results_bucket.bucket_id
    athena_database_name = var.athena_database_name
    athena_workgroup_name = var.athena_workgroup_name
}

# Data collection Lambda

module "lambda" {
    source = "./modules/lambda"
    region = var.region
    function_name = var.function_name
    cloudwatch_policy_name = var.cloudwatch_policy_name
    s3_policy_name = var.s3_policy_name
    athena_policy_name = var.athena_policy_name
    glue_policy_name = var.glue_policy_name
    athena_config_table_name = var.athena_config_table_name
    athena_cloudtrail_table_name = var.athena_cloudtrail_table_name
    athena_database_name = var.athena_database_name
    athena_workgroup_name = var.athena_workgroup_name
    athena_query_results_bucket_name = module.athena_query_results_bucket.bucket_id
    athena_query_results_bucket_arn = module.athena_query_results_bucket.bucket_arn
    data_collection_bucket_name = module.data_collection_bucket.bucket_id
}

# IAM Role for QuickSight data sources

data "aws_iam_policy" "qs_athena_full_access_policy" {
  arn = "arn:aws:iam::aws:policy/AmazonAthenaFullAccess"
}

data "aws_iam_policy_document" "qs_s3_policy_document" {

  statement {
    sid    = "Sid1"
    effect = "Allow"
    actions = [
        "s3:ListAllMyBuckets"
    ]
    resources = ["arn:aws:s3:::*"]
  }

  statement {
    sid    = "Sid2"
    effect = "Allow"
    actions = [
        "s3:ListBucket"
    ]
    resources = [module.athena_query_results_bucket.bucket_arn, module.data_collection_bucket.bucket_arn]
  }

  statement {
    sid    = "Sid3"
    effect = "Allow"
    actions = [
        "s3:GetObject",
        "s3:GetObjectVersion"
    ]
    resources = ["${module.athena_query_results_bucket.bucket_arn}/*", "${module.data_collection_bucket.bucket_arn}/*"]
  }

  statement {
    sid    = "Sid4"
    effect = "Allow"
    actions = [
        "s3:ListBucketMultipartUploads",
        "s3:GetBucketLocation"
    ]
    resources = ["${module.athena_query_results_bucket.bucket_arn}", "${module.data_collection_bucket.bucket_arn}"]
  }

  statement {
    sid    = "Sid5"
    effect = "Allow"
    actions = [
        "s3:PutObject",
        "s3:AbortMultipartUpload",
        "s3:ListMultipartUploadParts"
    ]
    resources = ["${module.athena_query_results_bucket.bucket_arn}/*", "${module.data_collection_bucket.bucket_arn}/*"]
  }
}

resource "aws_iam_policy" "qs_s3_policy" {
  name_prefix = "quicksight-datasource-s3-policy"
  description = "Policy that gives S3 permissisons to QuickSight IAM role"
  policy      = data.aws_iam_policy_document.qs_s3_policy_document.json
}

resource "aws_iam_role" "qs_role" {
  name = "quicksight-datasource-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "quicksight.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "qs_s3_policy_attachment" {
  policy_arn = aws_iam_policy.qs_s3_policy.arn
  role       = aws_iam_role.qs_role.name
}

resource "aws_iam_role_policy_attachment" "qs_athena_full_access" {
  policy_arn = data.aws_iam_policy.qs_athena_full_access_policy.arn
  role       = aws_iam_role.qs_role.name
}
