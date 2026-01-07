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

# Load .env and set up Terraform variables
load_env() {
    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        error "Missing .env file - copy from .env.example and fill in values"
    fi

    set -a
    source "$SCRIPT_DIR/.env"
    set +a

    if [ -z "$PERCEPTRON_API_KEY" ]; then
        error "PERCEPTRON_API_KEY not set in .env"
    fi

    if [ -z "$AWS_REGION" ]; then
        read -p "AWS region [us-west-2]: " AWS_REGION
        AWS_REGION="${AWS_REGION:-us-west-2}"
    fi

    export TF_VAR_aws_region="$AWS_REGION"
    export TF_VAR_perceptron_api_key="$PERCEPTRON_API_KEY"
    export TF_VAR_domain_name="$DOMAIN_NAME"
    export AWS_REGION

    log "Using AWS region: $AWS_REGION"
}

# Ensure AWS credentials are valid, prompting for SSO login if needed
aws_login() {
    if aws sts get-caller-identity &>/dev/null; then
        log "AWS credentials valid"
        return 0
    fi

    if [ -z "$AWS_PROFILE" ]; then
        PROFILES=$(grep '^\[profile ' ~/.aws/config 2>/dev/null | sed 's/\[profile \(.*\)\]/\1/' | tr '\n' ' ')
        if [ -n "$PROFILES" ]; then
            echo "Available profiles: $PROFILES"
            read -p "AWS profile name: " AWS_PROFILE
            export AWS_PROFILE
        fi
    fi

    if [ -n "$AWS_PROFILE" ]; then
        log "Logging in with profile: $AWS_PROFILE"
        aws sso login --profile "$AWS_PROFILE"
    else
        warn "No AWS profile configured. Setting up SSO..."
        aws configure sso
        read -p "Enter the profile name you just created: " AWS_PROFILE
        export AWS_PROFILE
    fi

    if ! aws sts get-caller-identity &>/dev/null; then
        error "AWS login failed. Try: export AWS_PROFILE=your-profile-name"
    fi
    log "AWS login successful (profile: $AWS_PROFILE)"
}

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
docker build --platform linux/arm64 --provenance=false -t ski-resort-analyzer "$SCRIPT_DIR/analysis"

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
