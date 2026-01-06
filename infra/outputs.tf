output "ecr_repository_url" {
  description = "ECR repository URL for pushing Docker images"
  value       = aws_ecr_repository.lambda.repository_url
}

output "s3_bucket_name" {
  description = "S3 bucket name for analysis results"
  value       = aws_s3_bucket.results.id
}

output "cloudfront_domain" {
  description = "CloudFront domain for accessing results"
  value       = aws_cloudfront_distribution.results.domain_name
}

output "cloudfront_url" {
  description = "Full URL to access analysis results"
  value       = "https://${aws_cloudfront_distribution.results.domain_name}/analysis_results.json"
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.analyzer.function_name
}
