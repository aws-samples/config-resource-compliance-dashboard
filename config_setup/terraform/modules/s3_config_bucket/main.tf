data aws_caller_identity current {}

# S3

resource "aws_s3_bucket" "s3_bucket" {

  #checkov:skip=CKV_AWS_144: Data is not critical, no need for cross region replication
  #checkov:skip=CKV_AWS_21: Logs are unique, no need for versioning
  #checkov:skip=CKV2_AWS_61: No need for lifecycle configuration
  #checkov:skip=CKV2_AWS_62: False positive: S3 bucket will have event notifications directly from the Lambda module
  #checkov:skip=CKV_AWS_18: False positive: Logging is enabled after the bucket are created with the "s3_logging" module
  #checkov:skip=CKV_AWS_145: Encryption with SSES3 is enough, no need for KMS

  bucket_prefix = var.bucket_prefix
  force_destroy = true

}

resource "aws_s3_bucket_server_side_encryption_configuration" "s3_bucket" {
  bucket = aws_s3_bucket.s3_bucket.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "s3_bucket_block_public_access" {
  bucket = aws_s3_bucket.s3_bucket.id
  
  restrict_public_buckets = true
  block_public_acls   = true
  block_public_policy = true
  ignore_public_acls=true
}

resource "aws_s3_bucket_policy" "s3_bucket_policy" {
  bucket = aws_s3_bucket.s3_bucket.id
  policy = data.aws_iam_policy_document.s3_bucket_policy_document.json
}

data "aws_iam_policy_document" "s3_bucket_policy_document" {
  statement {
    sid = "HTTPSOnly"
    principals {
      identifiers = ["*"]
      type        = "*"
    }

    actions = [
      "s3:*"
    ]
    
    effect = "Deny"

    resources = [
      aws_s3_bucket.s3_bucket.arn,
      "${aws_s3_bucket.s3_bucket.arn}/*",
    ]
    
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }

  statement {
    sid = "AWSConfigBucketPermissionsCheck"
    principals {
      identifiers = ["config.amazonaws.com"]
      type        = "Service"
    }

    actions = [
      "s3:GetBucketAcl"
    ]
    
    effect = "Allow"

    resources = [
      aws_s3_bucket.s3_bucket.arn
    ]
    
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceAccount"
      values   = ["${data.aws_caller_identity.current.account_id}"]
    }
  }

  statement {
    sid = "AWSConfigBucketExistenceCheck"
    principals {
      identifiers = ["config.amazonaws.com"]
      type        = "Service"
    }

    actions = [
      "s3:ListBucket"
    ]
    
    effect = "Allow"

    resources = [
      aws_s3_bucket.s3_bucket.arn
    ]
    
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceAccount"
      values   = ["${data.aws_caller_identity.current.account_id}"]
    }
  }

  statement {
    sid = "AWSConfigBucketDelivery"
    principals {
      identifiers = ["config.amazonaws.com"]
      type        = "Service"
    }

    actions = [
      "s3:PutObject"
    ]
    
    effect = "Allow"

    resources = [
      "${aws_s3_bucket.s3_bucket.arn}/*"
    ]
    
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceAccount"
      values   = ["${data.aws_caller_identity.current.account_id}"]
    }

    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }
  }
}
