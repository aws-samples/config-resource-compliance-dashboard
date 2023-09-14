terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  alias = "us-east-1"
}

provider "aws" {
  region = "us-east-2"
  alias = "us-east-2"
}

provider "aws" {
  region = "us-west-1"
  alias = "us-west-1"
}

provider "aws" {
  region = "us-west-2"
  alias = "us-west-2"
}

provider "aws" {
  region = "af-south-1"
  alias = "af-south-1"
}

provider "aws" {
  region = "ap-east-1"
  alias = "ap-east-1"
}

provider "aws" {
  region = "ap-south-2"
  alias = "ap-south-2"
}

provider "aws" {
  region = "ap-southeast-3"
  alias = "ap-southeast-3"
}

provider "aws" {
  region = "ap-southeast-4"
  alias = "ap-southeast-4"
}

provider "aws" {
  region = "ap-south-1"
  alias = "ap-south-1"
}

provider "aws" {
  region = "ap-northeast-3"
  alias = "ap-northeast-3"
}

provider "aws" {
  region = "ap-northeast-2"
  alias = "ap-northeast-2"
}

provider "aws" {
  region = "ap-southeast-1"
  alias = "ap-southeast-1"
}

provider "aws" {
  region = "ap-southeast-2"
  alias = "ap-southeast-2"
}

provider "aws" {
  region = "ap-northeast-1"
  alias = "ap-northeast-1"
}

provider "aws" {
  region = "ca-central-1"
  alias = "ca-central-1"
}

provider "aws" {
  region = "eu-central-1"
  alias = "eu-central-1"
}

provider "aws" {
  region = "eu-west-1"
  alias = "eu-west-1"
}

provider "aws" {
  region = "eu-west-2"
  alias = "eu-west-2"
}

provider "aws" {
  region = "eu-west-3"
  alias = "eu-west-3"
}

provider "aws" {
  region = "eu-south-1"
  alias = "eu-south-1"
}

provider "aws" {
  region = "eu-south-2"
  alias = "eu-south-2"
}

provider "aws" {
  region = "eu-north-1"
  alias = "eu-north-1"
}

provider "aws" {
  region = "eu-central-2"
  alias = "eu-central-2"
}

provider "aws" {
  region = "me-south-1"
  alias = "me-south-1"
}

provider "aws" {
  region = "me-central-1"
  alias = "me-central-1"
}

provider "aws" {
  region = "sa-east-1"
  alias = "sa-east-1"
}

provider "aws" {
  region = "us-gov-east-1"
  alias = "us-gov-east-1"
}

provider "aws" {
  region = "us-gov-west-1"
  alias = "us-gov-west-1"
}