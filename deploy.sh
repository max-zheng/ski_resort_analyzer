#!/bin/bash
set -e

# Build, push, and deploy ski resort analyzer to AWS
# Usage: ./deploy.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INFRA_DIR="$SCRIPT_DIR/infra"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[x]${NC} $1"; exit 1; }

# Source common functions
source "$SCRIPT_DIR/scripts/common.sh"

# Check prerequisites
command -v docker >/dev/null 2>&1 || error "Docker not installed"
command -v terraform >/dev/null 2>&1 || error "Terraform not installed"
command -v aws >/dev/null 2>&1 || error "AWS CLI not installed"

aws_login
load_env

# Deploy infrastructure
cd "$INFRA_DIR"
terraform init -input=false
terraform apply

ECR_URL=$(terraform output -raw ecr_repository_url)

# Build and push Docker image
log "Logging into ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_URL"

log "Building Docker image for arm64..."
cd "$SCRIPT_DIR"
docker build --platform linux/arm64 --provenance=false -t ski-resort-analyzer .

log "Pushing image..."
docker tag ski-resort-analyzer:latest "$ECR_URL:latest"
docker push "$ECR_URL:latest"

# Deploy frontend
log "Building frontend..."
cd "$SCRIPT_DIR/frontend"
npm run build

WEBSITE_BUCKET=$(cd "$INFRA_DIR" && terraform output -raw website_bucket_name)
log "Deploying frontend to S3..."
aws s3 sync dist "s3://$WEBSITE_BUCKET" --delete

# Invalidate CloudFront cache
DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Origins.Items[?contains(DomainName, '$WEBSITE_BUCKET')]].Id" --output text 2>/dev/null) || true
if [ -n "$DISTRIBUTION_ID" ]; then
    log "Invalidating CloudFront cache..."
    aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" --paths "/*" --no-cli-pager
fi
log "Frontend deployed."

cd "$INFRA_DIR"

# Update Lambda if image changed
FUNCTION_NAME=$(terraform output -raw lambda_function_name)

# Get current Lambda image digest
LAMBDA_DIGEST=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$AWS_REGION" --query 'Code.ImageUri' --output text 2>/dev/null | grep -oE '@sha256:[a-f0-9]+' || echo "")

# Get latest ECR image digest
ECR_DIGEST=$(aws ecr describe-images --repository-name ski-resort-analyzer --image-ids imageTag=latest --region "$AWS_REGION" --query 'imageDetails[0].imageDigest' --output text 2>/dev/null || echo "")

if [ -n "$ECR_DIGEST" ] && [ "$LAMBDA_DIGEST" != "@$ECR_DIGEST" ]; then
    log "Updating Lambda to latest image..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --image-uri "$ECR_URL:latest" \
        --region "$AWS_REGION" \
        --no-cli-pager
    log "Lambda updated."
else
    log "Lambda already running latest image."
fi

log "Deployment complete!"
