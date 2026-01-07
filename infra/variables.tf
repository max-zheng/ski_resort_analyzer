variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "ski-resort-analyzer"
}

variable "perceptron_api_key" {
  description = "API key for Perceptron"
  type        = string
  sensitive   = true
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 600  # 10 minutes
}

variable "lambda_memory" {
  description = "Lambda memory in MB"
  type        = number
  default     = 1024
}

variable "cloudfront_ttl" {
  description = "CloudFront cache TTL in seconds"
  type        = number
  default     = 300  # 5 minutes
}

variable "domain_name" {
  description = "Domain name for the website"
  type        = string
}
