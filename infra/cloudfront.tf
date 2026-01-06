# Origin Access Control for S3
resource "aws_cloudfront_origin_access_control" "results" {
  name                              = "${var.project_name}-oac"
  description                       = "OAC for ${var.project_name} S3 bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront distribution
resource "aws_cloudfront_distribution" "results" {
  enabled             = true
  comment             = "Ski Resort Analyzer Results"
  default_root_object = "analysis_results.json"
  price_class         = "PriceClass_200"

  origin {
    domain_name              = aws_s3_bucket.results.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.results.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.results.id
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.results.id}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy     = "redirect-to-https"
    min_ttl                    = 0
    default_ttl                = var.cloudfront_ttl
    max_ttl                    = var.cloudfront_ttl
    compress                   = true
    response_headers_policy_id = aws_cloudfront_response_headers_policy.cors.id
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

# CORS policy for API access
resource "aws_cloudfront_response_headers_policy" "cors" {
  name    = "${var.project_name}-cors-policy"
  comment = "CORS policy for ski resort analyzer"

  cors_config {
    access_control_allow_credentials = false

    access_control_allow_headers {
      items = ["*"]
    }

    access_control_allow_methods {
      items = ["GET", "HEAD", "OPTIONS"]
    }

    access_control_allow_origins {
      items = ["*"]
    }

    origin_override = true
  }
}
