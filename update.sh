#!/bin/bash
set -e

# Build and push Docker image to ECR
# Usage: ./update.sh

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
command -v aws >/dev/null 2>&1 || error "AWS CLI not installed"

aws_login
load_env

# Create ECR if it doesn't exist
cd "$INFRA_DIR"
if ! terraform output -raw ecr_repository_url &>/dev/null; then
    log "Creating ECR repository..."
    terraform init -input=false
    terraform apply -target=aws_ecr_repository.lambda -target=aws_ecr_lifecycle_policy.lambda -auto-approve
fi

ECR_URL=$(terraform output -raw ecr_repository_url)

# Build and push
log "Logging into ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_URL"

log "Building Docker image for arm64..."
cd "$SCRIPT_DIR"
docker build --platform linux/arm64 --provenance=false -t ski-resort-analyzer .

log "Pushing image..."
docker tag ski-resort-analyzer:latest "$ECR_URL:latest"
docker push "$ECR_URL:latest"

log "Image pushed. Run ./deploy.sh to deploy."
