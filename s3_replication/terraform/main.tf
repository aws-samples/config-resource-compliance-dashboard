# Get bucket ARNs

data "aws_s3_bucket" "data_source_bucket" {
  bucket = var.source_bucket_name
}

# IAM role

data "aws_iam_policy_document" "replication_role_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "replication_role" {
  name               = var.replication_role_name
  assume_role_policy = data.aws_iam_policy_document.replication_role_assume_role.json
}

data "aws_iam_policy_document" "replication_role_s3_permissions" {
  statement {
    effect = "Allow"

    actions = [
      "s3:GetReplicationConfiguration",
      "s3:ListBucket",
    ]

    resources = [data.aws_s3_bucket.data_source_bucket.arn]
  }

  statement {
    effect = "Allow"

    actions = [
      "s3:GetObjectVersionForReplication",
      "s3:GetObjectVersionAcl",
      "s3:GetObjectVersionTagging",
    ]

    resources = ["${data.aws_s3_bucket.data_source_bucket.arn}/*"]
  }

  statement {
    effect = "Allow"

    actions = [
      "s3:ReplicateObject",
      "s3:ReplicateDelete",
      "s3:ReplicateTags",
    ]

    resources = ["arn:aws:s3:::${var.destination_bucket_name}/*"]
  }
}

resource "aws_iam_policy" "replication_role_policy" {
  name   = "${var.replication_role_name}-policy"
  policy = data.aws_iam_policy_document.replication_role_s3_permissions.json
}

resource "aws_iam_role_policy_attachment" "replication_role_policy_attachment" {
  role       = aws_iam_role.replication_role.name
  policy_arn = aws_iam_policy.replication_role_policy.arn
}

# Replication configuration

resource "aws_s3_bucket_replication_configuration" "replication_configuration" {

  role   = aws_iam_role.replication_role.arn
  bucket = var.source_bucket_name

  rule {
    id = "replication_to_crcd_bucket"

    filter {
      prefix = "AWSLogs"
    }

    delete_marker_replication {
      status = "Enabled"
    }

    status = "Enabled"

    destination {
      bucket        = "arn:aws:s3:::${var.destination_bucket_name}"
      storage_class = "STANDARD"
    }
  }
}