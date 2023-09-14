data aws_caller_identity current {}

resource "aws_athena_workgroup" "athena_workgroup" {
  name = var.athena_workgroup_name
  force_destroy = true

  configuration {
    result_configuration {
      acl_configuration {
        s3_acl_option = "BUCKET_OWNER_FULL_CONTROL"
      }
      expected_bucket_owner = data.aws_caller_identity.current.account_id
      output_location = "s3://${var.athena_query_results_bucket_name}/"
      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }
}

resource "aws_athena_database" "athena_database" {
  name   = var.athena_database_name
  bucket = var.athena_query_results_bucket_name

  force_destroy = true
  encryption_configuration {
    encryption_option = "SSE_S3"
  }
}