#!/bin/bash
set -e

# Deploy ski resort analyzer infrastructure to AWS
# First time: ./update.sh → ./deploy.sh
# Code updates: ./update.sh → ./deploy.sh

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
command -v terraform >/dev/null 2>&1 || error "Terraform not installed"
command -v aws >/dev/null 2>&1 || error "AWS CLI not installed"

aws_login
load_env

cd "$INFRA_DIR"
terraform init
terraform apply

# Update Lambda if image changed
FUNCTION_NAME=$(terraform output -raw lambda_function_name 2>/dev/null) || exit 0
ECR_URL=$(terraform output -raw ecr_repository_url)

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
