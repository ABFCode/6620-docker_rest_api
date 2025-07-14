terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.3.0"
    }
  }
}

variable "localstack_s3_endpoint" {
  description = "The endpoint URL for the LocalStack S3 service."
  type        = string
  default     = "http://localhost:4566"
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    s3  = var.localstack_s3_endpoint
    sts = var.localstack_s3_endpoint
  }
}

resource "aws_s3_bucket" "test-bucket" {
  bucket = "my-books"
}