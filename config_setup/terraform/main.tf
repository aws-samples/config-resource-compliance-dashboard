# S3 buckets

module "logging_bucket" {

    source = "./modules/s3"
    bucket_prefix = "cid-config-logging"
}

module "data_collection_bucket" {

    source = "./modules/s3_config_bucket"
    bucket_prefix = "cid-config-data-collection"
}

module "data_collection_bucket_logging" {

    source = "./modules/s3_logging"
    bucket_name = module.data_collection_bucket.bucket_id
    logging_bucket_name = module.logging_bucket.bucket_id
}

## IAM Role

data "aws_iam_policy_document" "config_role_policy_document_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["config.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "config_role" {
  name               = "cid-config-role"
  assume_role_policy = data.aws_iam_policy_document.config_role_policy_document_assume_role.json
}

data "aws_iam_policy_document" "config_role_policy_document_s3" {
  statement {
    effect  = "Allow"
    actions = ["s3:*"]
    resources = [
      module.data_collection_bucket.bucket_arn,
      "${module.data_collection_bucket.bucket_arn}/*"
    ]
  }
}

resource "aws_iam_role_policy" "config_role_policy" {
  name   = "cid-config-policy"
  role   = aws_iam_role.config_role.id
  policy = data.aws_iam_policy_document.config_role_policy_document_s3.json
}

# Configuration Recorder. Add as many as required regions

module "configuration_recorder_eu_west_1" {

    source = "./modules/config_recorder"
    data_collection_bucket_name = module.data_collection_bucket.bucket_id
    iam_role_arn = aws_iam_role.config_role.arn

    providers = {
      aws = aws.eu-west-1
    }
}

module "configuration_recorder_eu_west_2" {

    source = "./modules/config_recorder"
    data_collection_bucket_name = module.data_collection_bucket.bucket_id
    iam_role_arn = aws_iam_role.config_role.arn

    providers = {
      aws = aws.eu-west-2
    }
}