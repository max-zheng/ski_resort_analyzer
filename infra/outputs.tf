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

# Website outputs
output "website_bucket_name" {
  description = "S3 bucket name for website files"
  value       = aws_s3_bucket.website.id
}

output "website_cloudfront_domain" {
  description = "CloudFront domain for the website"
  value       = aws_cloudfront_distribution.website.domain_name
}

output "website_url" {
  description = "Website URL"
  value       = "https://${var.domain_name}"
}

output "route53_nameservers" {
  description = "Route 53 nameservers for the domain"
  value       = data.aws_route53_zone.website.name_servers
}
