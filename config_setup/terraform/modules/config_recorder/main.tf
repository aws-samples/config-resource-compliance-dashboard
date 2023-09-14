terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

resource "aws_config_delivery_channel" "delivery_channel" {

  name           = "default"
  s3_bucket_name = var.data_collection_bucket_name

  snapshot_delivery_properties {
    delivery_frequency = "TwentyFour_Hours"
  }

  depends_on     = [aws_config_configuration_recorder.configuration_recorder]
}

resource "aws_config_configuration_recorder" "configuration_recorder" {

  name     = "default"
  role_arn = var.iam_role_arn

  recording_group {
    all_supported = true
    include_global_resource_types = true
  }
}